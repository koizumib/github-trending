"""data/repos/ の要約と、data/daily/ の errors の形を検査する。直しはしない。"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from .config import ROOT
from .storage import Store

SCHEMA_PATH = ROOT / "schemas" / "summary.schema.json"


def load_validator() -> Draft202012Validator:
    return Draft202012Validator(json.loads(SCHEMA_PATH.read_text(encoding="utf-8")))


def check_summary(path: Path, validator: Draft202012Validator) -> list[str]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return [f"JSON として読めない: {e}"]
    problems = [
        f"{'/'.join(map(str, err.path)) or '(全体)'}: {err.message}"
        for err in sorted(validator.iter_errors(obj), key=lambda e: list(e.path))
    ]
    if isinstance(obj, dict) and isinstance(obj.get("repo"), str):
        expected = obj["repo"].replace("/", "__") + ".json"
        if path.name != expected:
            problems.append(f"ファイル名は {expected} にする（repo と合わない）")
    try:
        dt.date.fromisoformat(obj.get("summarized_at", ""))
    except (TypeError, ValueError, AttributeError):
        problems.append("summarized_at: 日付として正しくない")
    return problems


def check_daily_errors(path: Path) -> list[str]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    errors = obj.get("errors", [])
    if not isinstance(errors, list):
        return ["errors: 配列にする"]
    return [
        f"errors[{i}]: {{\"repo\": ..., \"reason\": ...}} の形にする"
        for i, e in enumerate(errors)
        if not (isinstance(e, dict) and isinstance(e.get("repo"), str) and isinstance(e.get("reason"), str))
    ]


def validate_all(store: Store, work: Path | None = None) -> tuple[dict[str, list[str]], list[str]]:
    """(ファイルごとの問題, 注意) を返す。問題が1つでもあれば失敗とする。"""
    validator = load_validator()
    problems: dict[str, list[str]] = {}
    for path in sorted((store.dir / "repos").glob("*.json")):
        if found := check_summary(path, validator):
            problems[str(path.relative_to(store.dir.parent))] = found
    for path in sorted((store.dir / "daily").glob("*.json")):
        if found := check_daily_errors(path):
            problems[str(path.relative_to(store.dir.parent))] = found

    # queue のうち、要約も errors の記録もないもの（やり残し）は注意として出す
    notes: list[str] = []
    queue_path = (work or ROOT / ".work") / "queue.json"
    if queue_path.exists():
        queue = json.loads(queue_path.read_text(encoding="utf-8"))
        daily = store.load_daily(queue["date"]) or {}
        failed = {e.get("repo") for e in daily.get("errors", []) if isinstance(e, dict)}
        for item in queue["items"]:
            if store.load_summary(item["repo"]) is None and item["repo"] not in failed:
                notes.append(f"{item['repo']}: 要約も errors の記録もない")
    return problems, notes

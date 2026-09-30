"""data/ から site/ に静的 HTML を作る。入力が同じなら出力も同じ（生成時刻などは入れない）。"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup, escape

from .config import ROOT, Config
from .storage import Store

STATIC = Path(__file__).parent / "static"
STATUS_LABEL = {"new": "新着", "returning": "再登場", "continuing": "継続"}


def inline_code(text: str) -> Markup:
    """要約の中の `...` を <code> にする。ほかはすべてエスケープする。"""
    return Markup(re.sub(r"`([^`]+)`", r"<code>\1</code>", str(escape(text))))


def _env() -> Environment:
    env = Environment(
        loader=PackageLoader("trending_digest", "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.globals["status_label"] = STATUS_LABEL
    env.filters["code"] = inline_code
    return env


def _write(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def repo_href(repo: str) -> str:
    return f"r/{repo}/"


def build_day(store: Store, day: str) -> dict:
    """1日分の表示用データ。"""
    daily = store.load_daily(day) or {"date": day, "items": [], "errors": []}
    cards, others = [], []
    for item in daily["items"]:
        entry = dict(item, summary=store.load_summary(item["repo"]))
        (cards if item["status"] in ("new", "returning") else others).append(entry)
    return {
        "date": day,
        "cards": cards,
        "continuing": others,
        "errors": daily.get("errors", []),
        "count_new": sum(1 for c in cards if c["status"] == "new"),
        "count_continuing": len(others),
    }


def build(config: Config, store: Store | None = None, out: Path | None = None) -> Path:
    store = store or Store()
    out = out or ROOT / "site"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copy(STATIC / "style.css", out / "style.css")
    (out / ".nojekyll").write_text("")

    env = _env()
    days = store.list_days()
    history = store.load_history()
    pages = {name: env.get_template(f"{name}.html") for name in ("day", "repo", "archive")}

    # 日ごとのページと、いちばん新しい日をトップに
    summaries_by_day = []
    for i, day in enumerate(days):
        data = build_day(store, day)
        summaries_by_day.append(data)
        nav = {
            "newer": days[i - 1] if i > 0 else None,
            "older": days[i + 1] if i + 1 < len(days) else None,
        }
        _write(out / "d" / day / "index.html", pages["day"].render(root="../../", day=data, nav=nav, is_top=False))
        if i == 0:
            _write(out / "index.html", pages["day"].render(root="", day=data, nav=nav, is_top=True))
    if not days:
        _write(out / "index.html", pages["archive"].render(root="", days=[]))

    # リポジトリの詳しいページ（要約があるものすべて）
    latest_item = {}
    for data in reversed(summaries_by_day):  # 古い日から順に上書きし、最新の値を残す
        for item in data["cards"] + data["continuing"]:
            latest_item[item["repo"]] = item
    for path in sorted((store.dir / "repos").glob("*.json")):
        summary = store.load_summary(path.stem.replace("__", "/", 1))
        if summary is None:
            continue
        repo = summary["repo"]
        _write(out / "r" / repo / "index.html", pages["repo"].render(
            root="../../../", s=summary, item=latest_item.get(repo),
            seen=history.get(repo, {}).get("seen", []),
        ))

    _write(out / "archive" / "index.html", pages["archive"].render(root="../", days=summaries_by_day))
    return out

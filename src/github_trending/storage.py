"""data/ の読み書き。"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

from .config import ROOT

DATA_DIR = ROOT / "data"


def _read(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


class Store:
    def __init__(self, data_dir: Path = DATA_DIR):
        self.dir = data_dir

    # history.json
    def load_history(self) -> dict:
        return _read(self.dir / "history.json", {})

    def save_history(self, history: dict) -> None:
        _write(self.dir / "history.json", dict(sorted(history.items())))

    # daily/YYYY-MM-DD.json
    def daily_path(self, day: dt.date | str) -> Path:
        day = day if isinstance(day, str) else day.isoformat()
        return self.dir / "daily" / f"{day}.json"

    def save_daily(self, day: dt.date, items: list[dict]) -> None:
        """items を書く。同じ日に書き直しても、routine が書いた errors は残す。"""
        old = self.load_daily(day) or {}
        _write(self.daily_path(day), {
            "date": day.isoformat(),
            "items": items,
            "errors": old.get("errors", []),
        })

    def load_daily(self, day: dt.date | str) -> dict | None:
        return _read(self.daily_path(day), None)

    def list_days(self) -> list[str]:
        return sorted((p.stem for p in (self.dir / "daily").glob("*.json")), reverse=True)

    # weekly/YYYY-MM-DD.json、monthly/YYYY-MM-DD.json（その日に見た週・月の Trending）
    def period_path(self, period: str, day: dt.date | str) -> Path:
        day = day if isinstance(day, str) else day.isoformat()
        return self.dir / period / f"{day}.json"

    def save_period(self, period: str, day: dt.date, items: list[dict]) -> None:
        _write(self.period_path(period, day), {"date": day.isoformat(), "period": period, "items": items})

    def load_period(self, period: str, day: dt.date | str) -> dict | None:
        return _read(self.period_path(period, day), None)

    # repos/{owner}__{name}.json
    def repo_path(self, repo: str) -> Path:
        owner, name = repo.split("/", 1)
        return self.dir / "repos" / f"{owner}__{name}.json"

    def load_summary(self, repo: str) -> dict | None:
        return _read(self.repo_path(repo), None)

    def save_summary(self, summary: dict) -> None:
        _write(self.repo_path(summary["repo"]), summary)

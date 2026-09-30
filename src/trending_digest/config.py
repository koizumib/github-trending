"""config.yaml と日付の扱い。"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Config:
    new_window_days: int = 10
    model: str = "claude-sonnet-5-5"
    max_summaries_per_day: int = 15
    site_base_url: str = ""
    timezone: str = "Asia/Tokyo"

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)


def load_config(path: Path | None = None) -> Config:
    path = path or ROOT / "config.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    known = {k: v for k, v in raw.items() if k in Config.__dataclass_fields__}
    return Config(**known)


def today(tz: ZoneInfo, now: dt.datetime | None = None) -> dt.date:
    """「今日」を指定のタイムゾーンで決める。Actions は UTC で動くので必ずこれを使う。"""
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now にはタイムゾーン付きの datetime を渡す")
    return now.astimezone(tz).date()


def load_dotenv(path: Path | None = None) -> None:
    """.env を環境変数に読み込む（既に設定されているものは上書きしない）。値は表示しない。"""
    import os

    path = path or ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().removeprefix("export ").strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)

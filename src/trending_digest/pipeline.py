"""run の各段階をつなぐ。"""

from __future__ import annotations

import datetime as dt
import logging

from .classify import classify, update_history
from .config import Config
from .fetch_trending import TrendingItem
from .storage import Store

log = logging.getLogger(__name__)


def record(items: list[TrendingItem], day: dt.date, store: Store, config: Config) -> list[dict]:
    """分類して data/daily/ と history.json に書く。書いた items を返す。"""
    history = store.load_history()
    daily = []
    for item in items:
        d = item.to_dict()
        d["status"] = classify(item.repo, day, history, config.new_window_days)
        daily.append(d)
    store.save_daily(day, daily)
    store.save_history(update_history(history, [i.repo for i in items], day))
    counts = {s: sum(1 for d in daily if d["status"] == s) for s in ("new", "continuing", "returning")}
    log.info("%s: %d件（%s）", day, len(daily), ", ".join(f"{k} {v}" for k, v in counts.items()))
    return daily

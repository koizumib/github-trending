"""prepare の各段階をつなぐ。どれも入力が同じなら出力も同じになる。"""

from __future__ import annotations

import datetime as dt
import json
import logging
import shutil
from pathlib import Path

from .classify import CONTINUING, NEW, RETURNING, classify, update_history
from .config import Config
from .fetch_trending import TrendingItem
from .gather import Gatherer
from .storage import Store

log = logging.getLogger(__name__)

# 要約する順番：デイリーの new → returning → 前の日に回された continuing → ウィークリー → マンスリー
STATUS_ORDER = {NEW: 0, RETURNING: 1, CONTINUING: 2, "weekly": 3, "monthly": 4}


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
    counts = {s: sum(1 for d in daily if d["status"] == s) for s in (NEW, CONTINUING, RETURNING)}
    log.info("%s: %d件（%s）", day, len(daily), ", ".join(f"{k} {v}" for k, v in counts.items()))
    return daily


def pick_targets(
    daily: list[dict], store: Store, limit: int, periods: dict[str, list[dict]] | None = None,
) -> tuple[list[dict], list[dict]]:
    """要約がまだないものを選ぶ。順番は STATUS_ORDER、その中は順位順。同じリポジトリは1回だけ。

    ウィークリー・マンスリーにだけ出ているものは、status に "weekly" / "monthly" を入れる。
    上限を超えた分は deferred として返す（次の日に回る）。
    """
    candidates = list(daily)
    for period in ("weekly", "monthly"):
        candidates += [dict(d, status=period) for d in (periods or {}).get(period, [])]
    todo, seen = [], set()
    for d in sorted(candidates, key=lambda d: (STATUS_ORDER[d["status"]], d["rank"])):
        if d["repo"] in seen or store.load_summary(d["repo"]) is not None:
            continue
        seen.add(d["repo"])
        todo.append(d)
    return todo[:limit], todo[limit:]


def work_dir_name(repo: str) -> str:
    return repo.replace("/", "__")


def record_periods(periods: dict[str, list[TrendingItem]], day: dt.date, store: Store) -> dict[str, list[dict]]:
    """ウィークリー・マンスリーを data/weekly/、data/monthly/ に書く。分類はしない。"""
    written = {}
    for period, items in periods.items():
        rows = [i.to_period_dict() for i in items]
        store.save_period(period, day, rows)
        written[period] = rows
        log.info("%s %s: %d件", day, period, len(rows))
    return written


def prepare_queue(
    daily: list[dict], day: dt.date, store: Store, config: Config, work: Path,
    gatherer: Gatherer | None = None, periods: dict[str, list[dict]] | None = None,
) -> dict:
    """材料を .work/ に下集めし、.work/queue.json を書く。"""
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    targets, deferred = pick_targets(daily, store, config.max_summaries_per_day, periods)
    gatherer = gatherer or (Gatherer() if targets else None)

    queue_items = []
    for d in targets:
        name = work_dir_name(d["repo"])
        entry = {
            "repo": d["repo"], "rank": d["rank"], "status": d["status"],
            "work_dir": f".work/{name}", "output": f"data/repos/{name}.json",
        }
        try:
            entry.update(gatherer.gather(d["repo"], work / name))
        except Exception as e:  # noqa: BLE001  1件の失敗で止めない
            log.warning("%s の材料集めに失敗: %s", d["repo"], e)
            entry.update({"materials": [], "errors": [f"gather: {e}"]})
        queue_items.append(entry)
        log.info("%s: %s", d["repo"], ", ".join(entry["materials"]) or "材料なし")

    queue = {
        "date": day.isoformat(),
        "items": queue_items,
        "deferred": [d["repo"] for d in deferred],
    }
    (work / "queue.json").write_text(json.dumps(queue, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log.info("queue: %d件、次の日に回す: %d件", len(queue_items), len(deferred))
    return queue

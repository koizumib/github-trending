"""今日の Trending を過去の記録と比べて new / continuing / returning に分ける。

- new        ：過去 window_days 日に一度も上がっていない（初めて、または記録がない）
               ※ 記録はあるが window より前だけ、のときは returning
- continuing ：過去 window_days 日のうちに上がっている
- returning  ：window_days 日より前に上がったことはあるが、その後は上がっていない

「過去 window_days 日」は today の前日から window_days 日前まで（today 自身は含めない）。
同じ日に2回動かしても結果が変わらないように、today 以降の記録は見ない。
"""

from __future__ import annotations

import datetime as dt

NEW = "new"
CONTINUING = "continuing"
RETURNING = "returning"


def classify(repo: str, today: dt.date, history: dict, window_days: int) -> str:
    entry = history.get(repo)
    past = sorted(d for d in (entry or {}).get("seen", []) if dt.date.fromisoformat(d) < today)
    if not past:
        return NEW
    last = dt.date.fromisoformat(past[-1])
    if (today - last).days <= window_days:
        return CONTINUING
    return RETURNING


def update_history(history: dict, repos: list[str], today: dt.date) -> dict:
    """今日上がったものを history に足す（同じ日を二重に足さない）。"""
    day = today.isoformat()
    for repo in repos:
        entry = history.setdefault(repo, {"first_seen": day, "seen": []})
        if day not in entry["seen"]:
            entry["seen"].append(day)
            entry["seen"].sort()
        entry["first_seen"] = min(entry["first_seen"], entry["seen"][0])
    return history

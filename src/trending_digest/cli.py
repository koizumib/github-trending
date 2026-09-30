"""python -m trending_digest prepare / validate / build / notify"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
from pathlib import Path

from .config import ROOT, load_config, load_dotenv, today
from .fetch_trending import TrendingError, TrendingItem, fetch_html, parse_trending
from .pipeline import prepare_queue, record
from .storage import Store

log = logging.getLogger("trending_digest")

ITEM_FIELDS = TrendingItem.__dataclass_fields__


def cmd_prepare(args) -> int:
    config = load_config()
    store = Store()
    day = dt.date.fromisoformat(args.date) if args.date else today(config.tz)

    existing = store.load_daily(day)
    if existing and not args.html and not args.refetch:
        # Trending は1日1回だけ取りに行く。今日の分があればそれを使う
        log.info("%s の Trending は取得済みなので、data/daily/ のものを使う", day)
        items = [TrendingItem(**{k: v for k, v in d.items() if k in ITEM_FIELDS}) for d in existing["items"]]
    else:
        try:
            html = Path(args.html).read_text(encoding="utf-8") if args.html else fetch_html()
            items = parse_trending(html)
        except TrendingError as e:
            log.error("%s", e)
            return 1

    daily = record(items, day, store, config)
    prepare_queue(daily, day, store, config, ROOT / ".work")
    return 0


def cmd_validate(args) -> int:
    from .validate import validate_all

    problems, notes = validate_all(Store())
    for path, found in problems.items():
        print(f"NG {path}")
        for p in found:
            print(f"   - {p}")
    for n in notes:
        print(f"注意 {n}")
    if problems:
        print(f"{len(problems)} 個のファイルに問題がある")
        return 1
    print("OK")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trending_digest")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="取得・分類・材料の下集め → .work/queue.json")
    p.add_argument("--html", help="github.com/trending を取りに行かず、保存した HTML を使う")
    p.add_argument("--refetch", action="store_true", help="今日の分が取得済みでも取り直す")
    p.add_argument("--date", help="「今日」を YYYY-MM-DD で上書きする（試すとき用）")

    sub.add_parser("validate", help="data/repos/ の形を検査")
    sub.add_parser("build", help="data/ から site/ を作り直す")
    n = sub.add_parser("notify", help="Discord に送る")
    n.add_argument("--dry-run", action="store_true", help="送る内容を表示するだけ")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv()

    if args.command == "prepare":
        return cmd_prepare(args)
    if args.command == "validate":
        return cmd_validate(args)
    raise SystemExit(f"{args.command} はまだ作っていない")

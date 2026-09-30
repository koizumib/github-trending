"""python -m trending_digest run / build"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
from pathlib import Path

from .config import load_config, today
from .fetch_trending import TrendingError, fetch_html, parse_trending
from .pipeline import record
from .storage import Store

log = logging.getLogger("trending_digest")


def cmd_run(args) -> int:
    config = load_config()
    store = Store()
    day = dt.date.fromisoformat(args.date) if args.date else today(config.tz)

    try:
        html = Path(args.html).read_text(encoding="utf-8") if args.html else fetch_html()
        items = parse_trending(html)
    except TrendingError as e:
        log.error("%s", e)
        return 1

    record(items, day, store, config)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trending_digest")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="取得〜要約〜サイト生成〜通知")
    run.add_argument("--dry-run", action="store_true", help="通知を送らない")
    run.add_argument("--html", help="github.com/trending を取りに行かず、保存した HTML を使う")
    run.add_argument("--date", help="「今日」を YYYY-MM-DD で上書きする（試すとき用）")
    sub.add_parser("build", help="data/ から site/ を作り直す")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if args.command == "run":
        return cmd_run(args)
    raise SystemExit(f"{args.command} はまだ作っていない")

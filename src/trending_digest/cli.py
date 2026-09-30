"""python -m trending_digest run / build"""

from __future__ import annotations

import argparse
import logging


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trending_digest")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="取得〜要約〜サイト生成〜通知")
    run.add_argument("--dry-run", action="store_true", help="通知を送らない")
    sub.add_parser("build", help="data/ から site/ を作り直す")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    raise SystemExit(f"{args.command} はまだ作っていない")

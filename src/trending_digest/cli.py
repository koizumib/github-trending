"""python -m trending_digest prepare / validate / build / notify"""

from __future__ import annotations

import argparse
import datetime as dt
import logging
from pathlib import Path

from .config import ROOT, load_config, load_dotenv, today
from .fetch_trending import TrendingError, TrendingItem, fetch_html, parse_trending
from .net import PoliteClient
from .pipeline import prepare_queue, record, record_periods
from .storage import Store

log = logging.getLogger("trending_digest")

ITEM_FIELDS = TrendingItem.__dataclass_fields__


def _items_from(rows: list[dict]) -> list[TrendingItem]:
    out = []
    for d in rows:
        d = dict(d)
        if "stars_period" in d:
            d["stars_today"] = d.pop("stars_period")
        out.append(TrendingItem(**{k: v for k, v in d.items() if k in ITEM_FIELDS}))
    return out


def cmd_prepare(args) -> int:
    config = load_config()
    store = Store()
    day = dt.date.fromisoformat(args.date) if args.date else today(config.tz)
    client = PoliteClient()  # 3つのページを同じクライアントで、1秒以上空けて取りに行く

    # デイリー：読めなければはっきり失敗させる
    existing = store.load_daily(day)
    if existing and not args.html and not args.refetch:
        # Trending は1日1回だけ取りに行く。今日の分があればそれを使う
        log.info("%s の Trending は取得済みなので、data/daily/ のものを使う", day)
        items = _items_from(existing["items"])
    else:
        try:
            html = Path(args.html).read_text(encoding="utf-8") if args.html else fetch_html(client)
            items = parse_trending(html)
        except TrendingError as e:
            log.error("%s", e)
            return 1
    daily = record(items, day, store, config)

    # ウィークリー・マンスリー：読めなくても止めない
    periods: dict[str, list[TrendingItem]] = {}
    for period in ("weekly", "monthly"):
        saved = store.load_period(period, day)
        if saved and not args.refetch:
            periods[period] = _items_from(saved["items"])
            continue
        if args.html:  # 保存した HTML で試すときは取りに行かない
            continue
        try:
            periods[period] = parse_trending(fetch_html(client, period))
        except TrendingError as e:
            log.warning("%s（この期間は今日は飛ばす）", e)
    period_rows = record_periods(periods, day, store)

    prepare_queue(daily, day, store, config, ROOT / ".work", periods=period_rows)
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


def cmd_build(args) -> int:
    from .build_site import build

    out = build(load_config())
    print(f"{out} に書き出した")
    return 0


def cmd_notify(args) -> int:
    from .notify_discord import NotifyError, already_notified, build_messages, dump, mark_notified, post, webhook_url

    config = load_config()
    store = Store()
    day = args.date or today(config.tz).isoformat()

    if store.load_daily(day) is None:
        # routine がまだ今日の分を push していない。見張り（watchdog）が別に知らせるので、ここでは何もしない
        log.info("%s の data/daily/ がまだないので送らない", day)
        return 0
    if already_notified(store, day) and not args.force:
        log.info("%s は送信済み", day)
        return 0

    messages = build_messages(day, store, config.site_base_url)
    if args.dry_run:
        print(dump(messages))
        return 0
    try:
        post(messages, webhook_url())
    except NotifyError as e:
        log.error("%s", e)
        return 1
    mark_notified(store, day)
    log.info("%s の通知を %d 通送った", day, len(messages))
    return 0


def cmd_watchdog(args) -> int:
    """今日の data/daily/ がなければ、routine が動いていないと Discord に知らせる。"""
    from .notify_discord import NotifyError, alert_message, post, webhook_url

    config = load_config()
    day = args.date or today(config.tz).isoformat()
    if Store().load_daily(day) is not None:
        log.info("%s の分はある", day)
        return 0
    msg = alert_message(
        f"{day} の分がまだ届いていません。routine が動かなかったか、Trending を読み取れなかった可能性があります。"
        "Claude Code の routine の実行記録を確かめてください。"
    )
    if args.dry_run:
        print(msg["content"])
        return 0
    try:
        post([msg], webhook_url())
    except NotifyError as e:
        log.error("%s", e)
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trending_digest")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="取得（デイリー・ウィークリー・マンスリー）・分類・材料の下集め → .work/queue.json")
    p.add_argument("--html", help="github.com/trending を取りに行かず、保存した HTML を使う")
    p.add_argument("--refetch", action="store_true", help="今日の分が取得済みでも取り直す")
    p.add_argument("--date", help="「今日」を YYYY-MM-DD で上書きする（試すとき用）")

    sub.add_parser("validate", help="data/repos/ の形を検査")
    sub.add_parser("build", help="data/ から site/ を作り直す")
    n = sub.add_parser("notify", help="その日の分を Discord に送る（1日1回）")
    n.add_argument("--dry-run", action="store_true", help="送る内容を表示するだけ")
    n.add_argument("--force", action="store_true", help="送信済みの日でも送る")
    n.add_argument("--date", help="YYYY-MM-DD（省略すると日本時間の今日）")
    w = sub.add_parser("watchdog", help="今日の分がなければ Discord に知らせる")
    w.add_argument("--dry-run", action="store_true", help="送る内容を表示するだけ")
    w.add_argument("--date", help="YYYY-MM-DD（省略すると日本時間の今日）")

    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    load_dotenv()

    if args.command == "prepare":
        return cmd_prepare(args)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "build":
        return cmd_build(args)
    if args.command == "notify":
        return cmd_notify(args)
    if args.command == "watchdog":
        return cmd_watchdog(args)
    raise SystemExit(f"{args.command} はまだ作っていない")

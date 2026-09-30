import datetime as dt

from trending_digest.config import Config
from trending_digest.fetch_trending import parse_trending
from trending_digest.pipeline import record
from trending_digest.storage import Store


def test_record_two_days(tmp_path, trending_html):
    store = Store(tmp_path)
    config = Config(new_window_days=10)
    items = parse_trending(trending_html)

    day1 = dt.date(2026, 9, 30)
    daily = record(items, day1, store, config)
    assert all(d["status"] == "new" for d in daily)
    assert store.load_daily(day1)["date"] == "2026-09-30"

    # 翌日：同じ顔ぶれ + 1件新しいもの
    day2 = dt.date(2026, 10, 1)
    new_item = type(items[0])(rank=15, repo="x/brand-new", description="", language=None,
                              stars=1, stars_today=1)
    daily2 = record(items[:3] + [new_item], day2, store, config)
    assert [d["status"] for d in daily2] == ["continuing"] * 3 + ["new"]

    history = store.load_history()
    assert history["debpalash/VoiceStudio"]["seen"] == ["2026-09-30", "2026-10-01"]
    assert history["x/brand-new"]["first_seen"] == "2026-10-01"
    assert store.list_days() == ["2026-10-01", "2026-09-30"]

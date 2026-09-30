import datetime as dt
from pathlib import Path

import httpx
import pytest

from trending_digest.fetch_trending import TrendingError, fetch_html, parse_trending
from trending_digest.net import PoliteClient
from trending_digest.pipeline import pick_targets, record_periods
from trending_digest.storage import Store

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("period,count,first", [
    ("weekly", 18, "paperclipai/paperclip"),
    ("monthly", 23, "bilawalsidhu/gods-eye-view"),
])
def test_parse_saved_period_pages(period, count, first):
    items = parse_trending((FIXTURES / f"trending_{period}.html").read_text(encoding="utf-8"))
    assert len(items) == count
    assert items[0].repo == first
    assert items[0].stars_today and items[0].stars_today > 0  # その期間に増えたスター


def test_fetch_uses_since_param():
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, text="ok")

    client = PoliteClient(httpx.Client(transport=httpx.MockTransport(handler)), min_interval=0)
    fetch_html(client)
    fetch_html(client, "weekly")
    fetch_html(client, "monthly")
    assert seen == [
        "https://github.com/trending",
        "https://github.com/trending?since=weekly",
        "https://github.com/trending?since=monthly",
    ]


def test_fetch_error_names_period():
    client = PoliteClient(httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(503))), min_interval=0)
    with pytest.raises(TrendingError, match="weekly"):
        fetch_html(client, "weekly")


def test_record_periods_renames_stars(tmp_path):
    store = Store(tmp_path)
    items = parse_trending((FIXTURES / "trending_weekly.html").read_text(encoding="utf-8"))
    rows = record_periods({"weekly": items}, dt.date(2026, 9, 30), store)
    saved = store.load_period("weekly", "2026-09-30")
    assert saved["period"] == "weekly" and saved["items"] == rows["weekly"]
    assert "stars_period" in rows["weekly"][0] and "stars_today" not in rows["weekly"][0]


def test_pick_targets_daily_first_then_weekly_then_monthly(tmp_path):
    store = Store(tmp_path)
    store.save_summary({"repo": "w/done"})
    daily = [
        {"rank": 1, "repo": "d/new", "status": "new"},
        {"rank": 2, "repo": "d/cont", "status": "continuing"},
    ]
    periods = {
        "weekly": [
            {"rank": 1, "repo": "d/new"},   # デイリーと重なる → 1回だけ
            {"rank": 2, "repo": "w/done"},  # 要約済み → 飛ばす
            {"rank": 3, "repo": "w/only"},
        ],
        "monthly": [{"rank": 1, "repo": "m/only"}, {"rank": 2, "repo": "w/only"}],
    }
    targets, deferred = pick_targets(daily, store, limit=3, periods=periods)
    assert [(t["repo"], t["status"]) for t in targets] == [
        ("d/new", "new"), ("d/cont", "continuing"), ("w/only", "weekly"),
    ]
    assert [(d["repo"], d["status"]) for d in deferred] == [("m/only", "monthly")]

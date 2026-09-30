import datetime as dt
from zoneinfo import ZoneInfo

import pytest

from trending_digest.config import today

JST = ZoneInfo("Asia/Tokyo")
UTC = dt.timezone.utc


def test_actions_schedule_time_is_jst_morning():
    # cron の UTC 22:00 は日本時間の翌日 7:00
    assert today(JST, dt.datetime(2026, 9, 29, 22, 0, tzinfo=UTC)) == dt.date(2026, 9, 30)


def test_just_before_jst_midnight():
    # UTC 14:59:59 = JST 23:59:59
    assert today(JST, dt.datetime(2026, 9, 30, 14, 59, 59, tzinfo=UTC)) == dt.date(2026, 9, 30)


def test_just_at_jst_midnight():
    # UTC 15:00:00 = JST 0:00:00（翌日）
    assert today(JST, dt.datetime(2026, 9, 30, 15, 0, 0, tzinfo=UTC)) == dt.date(2026, 10, 1)


def test_utc_date_differs_from_jst_date():
    # UTC ではまだ 9/30 だが、日本では 10/1
    now = dt.datetime(2026, 9, 30, 23, 0, tzinfo=UTC)
    assert now.date() == dt.date(2026, 9, 30)
    assert today(JST, now) == dt.date(2026, 10, 1)


def test_naive_datetime_rejected():
    with pytest.raises(ValueError):
        today(JST, dt.datetime(2026, 9, 30, 12, 0))

import datetime as dt

from trending_digest.classify import CONTINUING, NEW, RETURNING, classify, update_history

TODAY = dt.date(2026, 9, 30)
W = 10


def hist(*days: str) -> dict:
    return {"o/r": {"first_seen": min(days), "seen": sorted(days)}}


def test_never_seen_is_new():
    assert classify("o/r", TODAY, {}, W) == NEW


def test_seen_yesterday_is_continuing():
    assert classify("o/r", TODAY, hist("2026-09-29"), W) == CONTINUING


def test_gap_within_window_is_continuing():
    # 3日前に上がり、昨日は上がっていない → 10日以内なので new ではない
    assert classify("o/r", TODAY, hist("2026-09-27"), W) == CONTINUING


def test_window_boundary_exactly_10_days_is_continuing():
    assert classify("o/r", TODAY, hist("2026-09-20"), W) == CONTINUING


def test_window_boundary_11_days_is_returning():
    assert classify("o/r", TODAY, hist("2026-09-19"), W) == RETURNING


def test_old_then_recent_uses_latest():
    assert classify("o/r", TODAY, hist("2026-08-01", "2026-09-25"), W) == CONTINUING


def test_rerun_same_day_keeps_new():
    # 同じ日に2回動かしても、今日の記録で continuing にならない
    h = update_history({}, ["o/r"], TODAY)
    assert classify("o/r", TODAY, h, W) == NEW


def test_rerun_same_day_keeps_returning():
    h = update_history(hist("2026-09-01"), ["o/r"], TODAY)
    assert classify("o/r", TODAY, h, W) == RETURNING


def test_window_across_month_boundary():
    today = dt.date(2026, 10, 3)
    assert classify("o/r", today, hist("2026-09-23"), W) == CONTINUING
    assert classify("o/r", today, hist("2026-09-22"), W) == RETURNING


def test_update_history_adds_once_and_keeps_first_seen():
    h = hist("2026-09-28")
    update_history(h, ["o/r", "a/b"], TODAY)
    update_history(h, ["o/r"], TODAY)
    assert h["o/r"] == {"first_seen": "2026-09-28", "seen": ["2026-09-28", "2026-09-30"]}
    assert h["a/b"] == {"first_seen": "2026-09-30", "seen": ["2026-09-30"]}

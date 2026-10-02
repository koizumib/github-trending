import datetime as dt
import json

import pytest

from github_trending import cli
from github_trending import notify_discord as nd
from github_trending.storage import Store


@pytest.fixture
def env(tmp_path, monkeypatch):
    store = Store(tmp_path / "data")
    monkeypatch.setattr(cli, "Store", lambda: store)
    sent = []
    monkeypatch.setattr(nd, "post", lambda messages, url: sent.extend(messages))
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test/hook")
    return store, sent


def item(rank, repo, status="new"):
    return {"rank": rank, "repo": repo, "status": status, "language": "Go", "stars": 1,
            "stars_today": 1, "description": "d"}


def test_no_daily_sends_alert(env):
    store, sent = env
    assert cli.main(["watchdog", "--date", "2026-10-01"]) == 0
    assert "まだ取得できていません" in sent[0]["content"]
    assert not nd.already_notified(store, "2026-10-01")


def test_already_notified_sends_nothing(env):
    store, sent = env
    store.save_daily(dt.date(2026, 10, 1), [item(1, "a/b")])
    nd.mark_notified(store, "2026-10-01")
    assert cli.main(["watchdog", "--date", "2026-10-01"]) == 0
    assert sent == []


def test_not_notified_sends_with_warning_and_records(env):
    store, sent = env
    store.save_daily(dt.date(2026, 10, 1), [item(1, "a/b"), item(2, "c/d")])
    store.save_summary({"repo": "a/b", "short": "要約", "tags": ["CLI"]})
    assert cli.main(["watchdog", "--date", "2026-10-01"]) == 0
    assert sent[0]["content"].startswith("⚠️ 9時までに要約が 1 件そろわなかった")
    assert "2026-10-01 の GitHub Trending" in sent[0]["content"]
    assert nd.already_notified(store, "2026-10-01")


def test_all_summarized_sends_without_warning(env):
    store, sent = env
    store.save_daily(dt.date(2026, 10, 1), [item(1, "a/b"), item(2, "c/d", "continuing")])
    store.save_summary({"repo": "a/b", "short": "要約", "tags": ["CLI"]})
    assert cli.main(["watchdog", "--date", "2026-10-01"]) == 0
    assert sent[0]["content"].startswith("**2026-10-01 の GitHub Trending**")


def test_alert_command(env):
    _, sent = env
    assert cli.main(["alert", "prepare が失敗"]) == 0
    assert sent == [{"content": "⚠️ github-trending：prepare が失敗"}]


def test_too_early_boundary():
    from zoneinfo import ZoneInfo

    jst = ZoneInfo("Asia/Tokyo")
    utc = dt.timezone.utc
    assert cli.too_early(jst, dt.datetime(2026, 9, 30, 15, 30, tzinfo=utc))       # JST 0:30
    assert cli.too_early(jst, dt.datetime(2026, 9, 30, 20, 59, 59, tzinfo=utc))   # JST 5:59:59
    assert not cli.too_early(jst, dt.datetime(2026, 9, 30, 21, 0, tzinfo=utc))    # JST 6:00
    assert not cli.too_early(jst, dt.datetime(2026, 9, 30, 22, 8, tzinfo=utc))    # JST 7:08（routine）


def test_notify_waits_until_morning(env, monkeypatch):
    store, sent = env
    store.save_daily(dt.date(2026, 10, 1), [item(1, "a/b")])
    monkeypatch.setattr(cli, "too_early", lambda tz, now=None: True)
    assert cli.main(["notify", "--date", "2026-10-01"]) == 0
    assert sent == [] and not nd.already_notified(store, "2026-10-01")
    # 手で送り直すときの --force は例外
    assert cli.main(["notify", "--date", "2026-10-01", "--force"]) == 0
    assert sent and nd.already_notified(store, "2026-10-01")


def test_notify_sends_in_the_morning(env, monkeypatch):
    store, sent = env
    store.save_daily(dt.date(2026, 10, 1), [item(1, "a/b")])
    monkeypatch.setattr(cli, "too_early", lambda tz, now=None: False)
    assert cli.main(["notify", "--date", "2026-10-01"]) == 0
    assert sent and nd.already_notified(store, "2026-10-01")

import datetime as dt
import json

import pytest

from trending_digest import cli
from trending_digest import notify_discord as nd
from trending_digest.storage import Store


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
    assert sent == [{"content": "⚠️ trending-digest：prepare が失敗"}]

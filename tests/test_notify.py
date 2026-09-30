import datetime as dt

import httpx
import pytest

from trending_digest import notify_discord as nd
from trending_digest.storage import Store

BASE = "https://example.github.io/td/"


def item(rank, repo, status="new", **kw):
    return dict({"rank": rank, "repo": repo, "status": status, "language": "Go", "stars": 1,
                 "stars_today": 100, "description": "desc"}, **kw)


def summary(repo, short="短い要約。" * 5):
    return {"repo": repo, "short": short, "tags": ["CLI", "インフラ・運用"]}


def test_header_embeds_and_continuing_line(tmp_path):
    store = Store(tmp_path)
    store.save_summary(summary("a/one"))
    store.save_daily(dt.date(2026, 9, 30), [
        item(1, "a/one"), item(2, "b/two"), item(3, "c/cont", "continuing"), item(4, "d/ret", "returning"),
    ])
    msgs = nd.build_messages("2026-09-30", store, BASE)
    assert len(msgs) == 1
    m = msgs[0]
    assert m["content"].startswith("**2026-09-30 の GitHub Trending**　新着 2件／継続 1件\n" + BASE)
    assert m["content"].endswith("継続：c/cont")
    e1, e2, e3 = m["embeds"]
    assert e1["url"] == BASE + "r/a/one/" and "CLI / インフラ・運用" in e1["footer"]["text"]
    assert e2["url"] == "https://github.com/b/two" and "まだ要約していません" in e2["description"]
    assert e3["title"].endswith("（再登場）")


def test_split_by_embed_count_and_chars(tmp_path):
    store = Store(tmp_path)
    items = [item(i, f"o/r{i}") for i in range(1, 26)]
    for i in items:
        store.save_summary(summary(i["repo"], short="あ" * 340))
    store.save_daily(dt.date(2026, 9, 30), items)
    msgs = nd.build_messages("2026-09-30", store, BASE)
    assert sum(len(m["embeds"]) for m in msgs) == 25
    for m in msgs:
        assert len(m["embeds"]) <= nd.MAX_EMBEDS
        total = len(m["content"]) + sum(nd._embed_len(e) for e in m["embeds"])
        assert total <= nd.MAX_CHARS


def test_many_failures_add_warning(tmp_path):
    store = Store(tmp_path)
    store.save_daily(dt.date(2026, 9, 30), [item(1, "a/b"), item(2, "c/d")])
    path = store.daily_path("2026-09-30")
    data = __import__("json").loads(path.read_text())
    data["errors"] = [{"repo": "a/b", "reason": "x"}, {"repo": "c/d", "reason": "y"}]
    path.write_text(__import__("json").dumps(data))
    msgs = nd.build_messages("2026-09-30", store, BASE)
    assert "要約に失敗したものが多い" in msgs[-1]["content"]


def test_notified_is_recorded_once(tmp_path):
    store = Store(tmp_path)
    assert not nd.already_notified(store, "2026-09-30")
    nd.mark_notified(store, "2026-09-30")
    nd.mark_notified(store, "2026-09-30")
    assert nd.already_notified(store, "2026-09-30")
    assert (tmp_path / "notified.json").read_text().count("2026-09-30") == 1


def test_post_retries_on_429_and_blocks_mentions(monkeypatch):
    monkeypatch.setattr(nd.time, "sleep", lambda s: None)
    calls = []

    def handler(request):
        calls.append(request)
        if len(calls) == 1:
            return httpx.Response(429, json={"retry_after": 0.1})
        return httpx.Response(204)

    nd.post([{"content": "hi"}], "https://discord.test/hook", httpx.Client(transport=httpx.MockTransport(handler)))
    assert len(calls) == 2
    assert b'"allowed_mentions":{"parse":[]}' in calls[-1].content.replace(b" ", b"")


def test_post_error_does_not_leak_url():
    secret = "https://discord.test/api/webhooks/123/SECRET-TOKEN"
    client = httpx.Client(transport=httpx.MockTransport(lambda r: httpx.Response(404)))
    with pytest.raises(nd.NotifyError) as e:
        nd.post([{"content": "hi"}], secret, client)
    assert "SECRET" not in str(e.value) and "404" in str(e.value)

import datetime as dt
import json

import httpx

from github_trending.config import Config
from github_trending.gather import Gatherer
from github_trending.net import PoliteClient
from github_trending.pipeline import pick_targets, prepare_queue
from github_trending.storage import Store

REPO_INFO = {
    "full_name": "o/r", "description": "A tool", "homepage": "https://example.com",
    "topics": ["cli"], "language": "Go", "stargazers_count": 10, "forks_count": 1,
    "created_at": "2026-09-01T00:00:00Z", "pushed_at": "2026-09-29T00:00:00Z",
    "default_branch": "main", "archived": False, "fork": False, "license": {"spdx_id": "MIT"},
}
TREE = {"truncated": False, "tree": [
    {"path": "README.md", "type": "blob"}, {"path": "go.mod", "type": "blob"},
    {"path": "cmd", "type": "tree"}, {"path": "cmd/r", "type": "tree"},
    {"path": "cmd/r/main.go", "type": "blob"},
]}


def fake_github(request: httpx.Request) -> httpx.Response:
    url = str(request.url)
    routes = {
        "https://api.github.com/repos/o/r": (200, REPO_INFO),
        "https://api.github.com/repos/o/r/git/trees/main?recursive=1": (200, TREE),
        "https://api.github.com/repos/o/r/releases/latest": (404, {}),
        "https://raw.githubusercontent.com/o/r/main/README.md": (200, "# r\nDoes things."),
        "https://raw.githubusercontent.com/o/r/main/go.mod": (200, "module example.com/r\n"),
    }
    if url not in routes:
        return httpx.Response(404)
    status, body = routes[url]
    if isinstance(body, str):
        return httpx.Response(status, text=body)
    return httpx.Response(status, json=body)


def gatherer() -> Gatherer:
    client = httpx.Client(transport=httpx.MockTransport(fake_github))
    return Gatherer(PoliteClient(client, min_interval=0))


def test_gather_writes_materials(tmp_path):
    result = gatherer().gather("o/r", tmp_path / "o__r")
    assert result["materials"] == ["meta", "tree", "readme", "manifest:go.mod"]
    assert result["errors"] == []  # リリースがない（404）のはエラーではない

    meta = json.loads((tmp_path / "o__r/meta.json").read_text())
    assert meta["license"] == "MIT" and meta["homepage"] == "https://example.com"
    tree = (tmp_path / "o__r/tree.txt").read_text()
    assert "cmd/r/" in tree and "cmd/r/main.go" not in tree  # 深さ2まで
    assert (tmp_path / "o__r/README.md").read_text().startswith("# r")


def test_gather_failure_does_not_stop_queue(tmp_path):
    store = Store(tmp_path / "data")
    daily = [
        {"rank": 1, "repo": "gone/away", "status": "new"},
        {"rank": 2, "repo": "o/r", "status": "new"},
    ]
    queue = prepare_queue(daily, dt.date(2026, 9, 30), store, Config(), tmp_path / ".work", gatherer())
    by_repo = {q["repo"]: q for q in queue["items"]}
    assert by_repo["gone/away"]["materials"] == []
    assert "gather" in by_repo["gone/away"]["errors"][0]
    assert by_repo["o/r"]["materials"][0] == "meta"
    assert by_repo["o/r"]["output"] == "data/repos/o__r.json"
    assert json.loads((tmp_path / ".work/queue.json").read_text())["date"] == "2026-09-30"


def test_pick_targets_skips_summarized_and_defers_over_limit(tmp_path):
    store = Store(tmp_path)
    store.save_summary({"repo": "a/done"})
    daily = [
        {"rank": 1, "repo": "a/done", "status": "new"},
        {"rank": 2, "repo": "b/cont", "status": "continuing"},  # 前の日に回されたもの
        {"rank": 3, "repo": "c/new", "status": "new"},
        {"rank": 4, "repo": "d/ret", "status": "returning"},
        {"rank": 5, "repo": "e/new", "status": "new"},
    ]
    targets, deferred = pick_targets(daily, store, limit=3)
    assert [t["repo"] for t in targets] == ["c/new", "e/new", "d/ret"]
    assert [d["repo"] for d in deferred] == ["b/cont"]


def test_pick_readme_prefers_plain_name():
    from github_trending.gather import pick_readme

    assert pick_readme({"README-NIX.md", "README.md", "README.zh-CN.md"}) == "README.md"
    assert pick_readme({"readme.rst", "src/"}) == "readme.rst"
    assert pick_readme({"README_ja.md"}) == "README_ja.md"
    assert pick_readme({"main.go"}) is None


def test_pick_targets_refreshes_stale_summaries_after_new_ones(tmp_path):
    store = Store(tmp_path)
    day = dt.date(2026, 12, 29)
    store.save_summary({"repo": "a/old", "summarized_at": "2026-09-30"})     # 90日前：書き直す
    store.save_summary({"repo": "b/recent", "summarized_at": "2026-10-01"})  # 89日前：使い回す
    daily = [
        {"rank": 1, "repo": "a/old", "status": "returning"},
        {"rank": 2, "repo": "b/recent", "status": "returning"},
        {"rank": 3, "repo": "c/new", "status": "new"},
    ]
    targets, deferred = pick_targets(daily, store, limit=5, day=day, stale_days=90)
    assert [(t["repo"], t["refresh"]) for t in targets] == [("c/new", False), ("a/old", True)]
    # 上限が足りなければ、書き直しの方が次の日に回る
    targets, deferred = pick_targets(daily, store, limit=1, day=day, stale_days=90)
    assert [t["repo"] for t in targets] == ["c/new"] and [d["repo"] for d in deferred] == ["a/old"]
    # 日付を渡さなければ書き直さない
    targets, _ = pick_targets(daily, store, limit=5)
    assert [t["repo"] for t in targets] == ["c/new"]

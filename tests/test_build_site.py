import datetime as dt

from trending_digest.build_site import build, inline_code
from trending_digest.config import Config
from trending_digest.storage import Store

SUMMARY = {
    "repo": "o/r", "summarized_at": "2026-09-30", "short": "負荷をかける CLI。<b>太字</b>にはしない。",
    "what": "HTTP の負荷試験 CLI。", "can_do": ["同時接続"], "how_to_use": "`go install example.com/r@latest` で入る。",
    "use_cases": [], "for_whom": "", "similar": [], "tech": "Go", "caveats": "",
    "tags": ["CLI", "インフラ・運用"], "sources": ["readme"], "confidence": "low", "confidence_note": "README がほぼ空",
}


def make_store(tmp_path) -> Store:
    store = Store(tmp_path / "data")
    store.save_summary(SUMMARY)
    store.save_daily(dt.date(2026, 9, 29), [
        {"rank": 1, "repo": "o/r", "status": "new", "language": "Go", "stars": 10, "stars_today": 5, "description": "x"},
    ])
    store.save_daily(dt.date(2026, 9, 30), [
        {"rank": 1, "repo": "n/ew", "status": "new", "language": None, "stars": 1, "stars_today": 1, "description": "A new tool"},
        {"rank": 2, "repo": "o/r", "status": "continuing", "language": "Go", "stars": 20, "stars_today": 3, "description": "x"},
    ])
    store.save_history({"o/r": {"first_seen": "2026-09-29", "seen": ["2026-09-29", "2026-09-30"]}})
    return store


def test_build_pages(tmp_path):
    out = build(Config(), make_store(tmp_path), tmp_path / "site")
    index = (out / "index.html").read_text()
    assert "2026-09-30" in index
    assert "まだ要約していません" in index and "A new tool" in index  # 要約のない new
    assert 'href="r/o/r/"' in index  # continuing は名前だけ、詳しいページへ
    assert (out / "d/2026-09-29/index.html").exists()

    repo = (out / "r/o/r/index.html").read_text()
    assert "https://github.com/o/r" in repo
    assert "情報が少ない" in repo and "README がほぼ空" in repo
    assert "&lt;b&gt;" in repo and "<b>太字" not in repo  # エスケープされる
    assert "<code>go install example.com/r@latest</code>" in repo
    assert 'href="../../../d/2026-09-29/"' in repo

    archive = (out / "archive/index.html").read_text()
    assert archive.index("2026-09-30") < archive.index("2026-09-29")


def test_build_is_deterministic(tmp_path):
    store = make_store(tmp_path)
    a = build(Config(), store, tmp_path / "a")
    b = build(Config(), store, tmp_path / "b")
    files = sorted(p.relative_to(a) for p in a.rglob("*") if p.is_file())
    assert files == sorted(p.relative_to(b) for p in b.rglob("*") if p.is_file())
    assert all((a / f).read_bytes() == (b / f).read_bytes() for f in files)


def test_inline_code_escapes_inside():
    assert str(inline_code("`a<b` & c")) == "<code>a&lt;b</code> &amp; c"


def test_tags_shown_on_card_and_detail(tmp_path):
    out = build(Config(), make_store(tmp_path), tmp_path / "site")
    day = (out / "d/2026-09-29/index.html").read_text()
    assert "<li>CLI</li><li>インフラ・運用</li>" in day
    assert "<li>インフラ・運用</li>" in (out / "r/o/r/index.html").read_text()


def test_weekly_and_monthly_pages_with_tabs(tmp_path):
    store = make_store(tmp_path)
    store.save_period("weekly", dt.date(2026, 9, 30), [
        {"rank": 1, "repo": "o/r", "description": "x", "language": "Go", "stars": 20, "stars_period": 900},
        {"rank": 2, "repo": "w/eek", "description": "weekly only", "language": None, "stars": 5, "stars_period": 50},
    ])
    out = build(Config(), store, tmp_path / "site")

    weekly = (out / "weekly/index.html").read_text()
    assert "★ 今週 +900" in weekly and "weekly only" in weekly
    assert 'href="../r/o/r/"' in weekly  # 要約があるものは詳しいページへ
    assert (out / "d/2026-09-30/weekly/index.html").exists()
    assert 'href="../../../r/o/r/"' in (out / "d/2026-09-30/weekly/index.html").read_text()

    # マンスリーはデータがないので、タブは押せない形で出てページは作らない
    index = (out / "index.html").read_text()
    assert 'href="weekly/"' in index and '<span class="tab disabled">マンスリー</span>' in index
    assert not (out / "monthly").exists()
    # 9/29 にはウィークリーがないので、その日のページではウィークリーのタブも押せない
    assert '<span class="tab disabled">ウィークリー</span>' in (out / "d/2026-09-29/index.html").read_text()

    archive = (out / "archive/index.html").read_text()
    assert 'href="../d/2026-09-30/weekly/"' in archive
    assert 'href="../d/2026-09-29/weekly/"' not in archive

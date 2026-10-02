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
    assert "★ 今週 <b>+900</b>" in weekly and "weekly only" in weekly
    assert 'href="../r/o/r/"' in weekly  # 要約があるものは詳しいページへ
    assert (out / "d/2026-09-30/weekly/index.html").exists()
    assert 'href="../../../r/o/r/"' in (out / "d/2026-09-30/weekly/index.html").read_text()

    # マンスリーはデータがないので、タブは押せない形で出てページは作らない
    index = (out / "index.html").read_text()
    assert 'href="weekly/"' in index and '<span class="tab disabled">月次</span>' in index
    assert not (out / "monthly").exists()
    # 9/29 にはウィークリーがないので、その日のページではウィークリーのタブも押せない
    day29 = (out / "d/2026-09-29/index.html").read_text()
    assert '<span class="tab disabled">週次</span>' in day29

    # デイリーのタブは、トップ（最新の日）だけ「本日」、日ごとのページは「日次」
    assert '<span class="tab active" aria-current="page">本日</span>' in index
    assert '<span class="tab active" aria-current="page">日次</span>' in day29

    archive = (out / "archive/index.html").read_text()
    assert 'href="../d/2026-09-30/weekly/"' in archive
    assert 'href="../d/2026-09-29/weekly/"' not in archive


def test_issue_number_and_field_box(tmp_path):
    from trending_digest.build_site import count_fields

    items = [
        {"summary": {"tags": ["LLM", "CLI"]}}, {"summary": {"tags": ["LLM"]}},
        {"summary": None}, {"summary": {"tags": ["AI エージェント"]}},
    ]
    assert count_fields(items) == [("LLM", 2), ("AI エージェント", 1), ("CLI", 1)]

    out = build(Config(), make_store(tmp_path), tmp_path / "site")
    index = (out / "index.html").read_text()          # 最新の日（9/30）は2日目
    assert "第2号" in index
    assert "第1号" in (out / "d/2026-09-29/index.html").read_text()
    assert "第2号" in (out / "r/o/r/index.html").read_text()  # 詳しいページは最新の日の号数
    # 9/30 の記事：o/r（継続、要約あり：CLI・インフラ・運用）
    assert "本日の分野" in index and "<span>CLI</span><b>1</b>" in index
    assert "この日の分野" in (out / "d/2026-09-30/index.html").read_text()


def test_rank_tiers_and_language_color(tmp_path):
    from trending_digest.build_site import lang_color, rank_tier

    assert [rank_tier(r) for r in (1, 2, 3, 4, 5, 6, 25)] == ["xl", "l", "l", "m", "m", "s", "s"]
    assert lang_color("Python") == "#3572A5" and lang_color(None) == lang_color("Brainfuck") == "#9A9A9A"
    out = build(Config(), make_store(tmp_path), tmp_path / "site")
    index = (out / "index.html").read_text()
    assert 'class="card tier-xl"' in index  # 1位の記事
    assert 'class="rank" aria-label="1位">1<small>位</small>' in index


def test_marks_and_moves_across_days(tmp_path):
    from trending_digest.build_site import annotate_marks, build_page

    store = Store(tmp_path / "data")
    def day(d, repos):
        store.save_daily(dt.date.fromisoformat(d), [
            {"rank": i, "repo": r, "status": "new", "language": None, "stars": 1, "stars_today": 1, "description": ""}
            for i, r in enumerate(repos, start=1)])
    day("2026-09-28", ["a/a", "b/b", "c/c"])
    day("2026-09-29", ["b/b", "a/a", "d/d"])          # c/c は圏外に
    day("2026-09-30", ["a/a", "c/c", "b/b", "e/e"])   # c/c が戻る
    days = store.list_days()
    pages = {(d, p): build_page(store, d, p) for d in days for p in ("daily", "weekly", "monthly")}
    annotate_marks(pages, days)

    first = {c["repo"]: (c["mark"], c["move"]) for c in pages[("2026-09-28", "daily")]["cards"]}
    assert set(first.values()) == {("new", None)}  # 記録の初日は全部「新」

    mid = {c["repo"]: (c["mark"], c["move"]) for c in pages[("2026-09-29", "daily")]["cards"]}
    assert mid == {"b/b": ("continuing", 1), "a/a": ("continuing", -1), "d/d": ("new", None)}

    last = pages[("2026-09-30", "daily")]
    marks = {c["repo"]: (c["mark"], c["move"]) for c in last["cards"]}
    assert marks == {
        "a/a": ("continuing", 1),    # 2位 → 1位
        "c/c": ("returning", None),  # 9/28 にあり、9/29 は圏外
        "b/b": ("continuing", -2),   # 1位 → 3位
        "e/e": ("new", None),
    }
    assert (last["count_new"], last["count_continuing"], last["count_returning"]) == (1, 2, 1)

    out = build(Config(), store, tmp_path / "site")
    html = (out / "index.html").read_text()
    assert "▲1" in html and "▼2" in html and 'class="mark mark-returning"' in html
    assert "4件（新 1・続 2・再 1）" in html


def test_dropcap_wraps_first_char_or_first_word():
    from trending_digest.build_site import dropcap

    assert dropcap("声のクローン") == '<span class="drop">声</span>のクローン'
    assert dropcap("イリノイ大学") == '<span class="drop">イ</span>リノイ大学'
    # 英字で始まるときは単語ごと（1文字目だけだと単語が割れる）
    assert dropcap("AI エージェント") == '<span class="drop drop-word">AI</span> エージェント'
    assert dropcap("MySQL、") == '<span class="drop drop-word">MySQL</span>、'
    assert dropcap("C++ の") == '<span class="drop drop-word">C++</span> の'
    assert dropcap("Node.js. で") == '<span class="drop drop-word">Node.js</span>. で'
    # 長い単語、` で始まる文、空は飾らない
    assert "drop" not in dropcap("Kubernetesoperator を")
    assert dropcap("`wt` で") == "<code>wt</code> で"
    assert dropcap("") == ""
    # 残りは今までどおりエスケープし、` を <code> に
    assert dropcap("AI <b> と `x`") == '<span class="drop drop-word">AI</span> &lt;b&gt; と <code>x</code>'


def test_whole_card_links_to_detail_only_when_summarized(tmp_path):
    out = build(Config(), make_store(tmp_path), tmp_path / "site")
    day29 = (out / "d/2026-09-29/index.html").read_text()   # o/r は要約あり
    assert 'class="card tier-xl has-detail"' in day29
    index = (out / "index.html").read_text()                # 1位 n/ew は要約なし
    assert 'class="card tier-xl"' in index and "この日のページ" not in index


def test_page_title_is_just_the_name(tmp_path):
    out = build(Config(), make_store(tmp_path), tmp_path / "site")
    assert "<title>github新聞</title>" in (out / "d/2026-09-29/index.html").read_text()

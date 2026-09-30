"""data/ から site/ に静的 HTML を作る。入力が同じなら出力も同じ（生成時刻などは入れない）。"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from markupsafe import Markup, escape

from .config import ROOT, Config
from .storage import Store

STATIC = Path(__file__).parent / "static"
STATUS_LABEL = {"new": "新着", "returning": "再登場", "continuing": "継続"}


def inline_code(text: str) -> Markup:
    """要約の中の `...` を <code> にする。ほかはすべてエスケープする。"""
    return Markup(re.sub(r"`([^`]+)`", r"<code>\1</code>", str(escape(text))))


WEEKDAYS = "月火水木金土日"


def ja_date(day: str) -> str:
    """2026-09-30 → 2026年9月30日（水）"""
    import datetime as dt

    d = dt.date.fromisoformat(day)
    return f"{d.year}年{d.month}月{d.day}日（{WEEKDAYS[d.weekday()]}）"


def ja_ymd(day: str) -> str:
    """2026-09-30 → 2026年9月30日"""
    import datetime as dt

    d = dt.date.fromisoformat(day)
    return f"{d.year}年{d.month}月{d.day}日"


def ja_weekday(day: str) -> str:
    """2026-09-30 → 水曜日"""
    import datetime as dt

    return f"{WEEKDAYS[dt.date.fromisoformat(day).weekday()]}曜日"


def headline(text: str) -> str:
    """見出しにするため、末尾の句点を取る（新聞の見出しには「。」を付けない）。"""
    return text.strip().rstrip("。．.")


def starts_cjk(text: str) -> bool:
    """最初の1文字が日本語（ひらがな・カタカナ・漢字）か。英字で始まる文は大きな1文字目にしない（単語が割れるため）。"""
    return bool(text) and ("぀" <= text[0] <= "ヿ" or "一" <= text[0] <= "鿿")


def repo_wbr(repo: str) -> Markup:
    """owner/name の「/」の後ろで折り返せるようにする（名前の途中で折れないように）。"""
    owner, _, name = repo.partition("/")
    return Markup(f"{escape(owner)}/<wbr>{escape(name)}")


# 期間の呼び名。トップ（最新の日）のデイリーだけは「本日」と出す（テンプレートで）
PERIOD_NAME = {"daily": "日次", "weekly": "週次", "monthly": "月次"}

# 言語の色（GitHub で見慣れた色に近いもの）。ないものは灰色
LANG_COLORS = {
    "Python": "#3572A5", "TypeScript": "#3178C6", "JavaScript": "#F1E05A", "Rust": "#DEA584",
    "Go": "#00ADD8", "C": "#555555", "C++": "#F34B7D", "C#": "#178600", "Java": "#B07219",
    "Kotlin": "#A97BFF", "Swift": "#F05138", "Ruby": "#701516", "PHP": "#4F5D95",
    "Shell": "#89E051", "HTML": "#E34C26", "CSS": "#663399", "Vue": "#41B883", "Svelte": "#FF3E00",
    "Dart": "#00B4AB", "Zig": "#EC915C", "Lua": "#000080", "Jupyter Notebook": "#DA5B0B",
    "TeX": "#3D6117", "Scala": "#C22D40", "Elixir": "#6E4A7E", "Haskell": "#5E5086",
    "Nix": "#7E7EFF", "Julia": "#A270BA", "MDX": "#FCB32C", "Dockerfile": "#384D54",
}


def lang_color(language: str | None) -> str:
    return LANG_COLORS.get(language or "", "#9A9A9A")


def rank_tier(rank: int) -> str:
    """順位の数字の大きさ：1位は特大、2〜3位は大、4〜5位は中、ほかは小。"""
    if rank == 1:
        return "xl"
    if rank <= 3:
        return "l"
    if rank <= 5:
        return "m"
    return "s"


def _env() -> Environment:
    env = Environment(
        loader=PackageLoader("trending_digest", "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    env.globals["status_label"] = STATUS_LABEL
    env.globals["period_name"] = PERIOD_NAME
    env.filters["code"] = inline_code
    env.filters["ja_date"] = ja_date
    env.filters["ja_ymd"] = ja_ymd
    env.filters["ja_weekday"] = ja_weekday
    env.filters["wbr"] = repo_wbr
    env.filters["headline"] = headline
    env.tests["cjk_start"] = starts_cjk
    env.filters["lang_color"] = lang_color
    env.filters["rank_tier"] = rank_tier
    return env


def _write(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


PERIODS = ("daily", "weekly", "monthly")


def dated_href(day: str, period: str) -> str:
    return f"d/{day}/" if period == "daily" else f"d/{day}/{period}/"


def top_href(period: str) -> str:
    return "" if period == "daily" else f"{period}/"


def depth_root(href: str) -> str:
    return "../" * href.count("/")


def build_page(store: Store, day: str, period: str) -> dict | None:
    """1日1期間分の表示用データ。その期間のデータがなければ None。"""
    if period == "daily":
        raw = store.load_daily(day) or {"date": day, "items": [], "errors": []}
    else:
        raw = store.load_period(period, day)
        if raw is None:
            return None
    # 全件を順位どおりに記事として並べる（0019）。印（mark・move）は annotate_marks が付ける
    cards = [dict(item, summary=store.load_summary(item["repo"])) for item in raw["items"]]
    return {
        "date": day,
        "period": period,
        "cards": cards,
        "errors": raw.get("errors", []) if period == "daily" else [],
        "dated_href": dated_href(day, period),
        "fields": count_fields(cards),
    }


def annotate_marks(pages: dict, days: list[str]) -> None:
    """順位の下の印を付ける（0019）。同じ期間の、その日より前でいちばん新しい記録と比べる。

    - mark：「continuing」前回もランク入り／「new」初めて／「returning」以前はあったが前回は圏外
    - move：前回もランク入りしていれば、順位の差（正なら上がった）
    ページごとに count_new・count_continuing・count_returning も付ける。
    """
    for period in PERIODS:
        prev_rank: dict[str, int] | None = None
        ever: set[str] = set()
        for day in sorted(days):
            page = pages.get((day, period))
            if page is None:
                continue
            for c in page["cards"]:
                repo = c["repo"]
                if prev_rank is not None and repo in prev_rank:
                    c["mark"], c["move"] = "continuing", prev_rank[repo] - c["rank"]
                elif repo in ever:
                    c["mark"], c["move"] = "returning", None
                else:
                    c["mark"], c["move"] = "new", None
            for key in ("new", "continuing", "returning"):
                page[f"count_{key}"] = sum(1 for c in page["cards"] if c["mark"] == key)
            prev_rank = {c["repo"]: c["rank"] for c in page["cards"]}
            ever |= set(prev_rank)


def count_fields(items: list[dict], limit: int = 6) -> list[tuple[str, int]]:
    """要約のタグを数えて、多い順に返す（「本日の分野」の囲み）。同じ数なら名前順。"""
    from collections import Counter

    counts = Counter(t for i in items if i.get("summary") for t in i["summary"].get("tags") or [])
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]


def asset_versions() -> dict[str, str]:
    """静的ファイルごとに、中身から作った短い印（ファイル名 → 8桁）。

    URL に `?v=印` を付けると、中身が変わったときだけ URL が変わり、古いキャッシュが使われない。
    """
    import hashlib

    return {
        f.name: hashlib.sha256(f.read_bytes()).hexdigest()[:8]
        for f in sorted(STATIC.iterdir()) if f.is_file()
    }


def build(config: Config, store: Store | None = None, out: Path | None = None) -> Path:
    store = store or Store()
    out = out or ROOT / "site"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for f in sorted(STATIC.iterdir()):  # style.css とロゴ
        if f.is_file():
            shutil.copy(f, out / f.name)
    (out / ".nojekyll").write_text("")

    env = _env()
    days = store.list_days()
    env.globals["latest_day"] = days[0] if days else None  # ヘッダの日付（日ごとのページ以外）
    env.globals["issue_no"] = {d: n for n, d in enumerate(sorted(days), start=1)}  # 号数：最初の日が第1号
    env.globals["asset_v"] = asset_versions()  # CSS・ロゴの URL に付ける版の印
    history = store.load_history()
    day_tpl, repo_tpl, archive_tpl = (env.get_template(f"{n}.html") for n in ("day", "repo", "archive"))

    pages = {(d, p): build_page(store, d, p) for d in days for p in PERIODS}
    annotate_marks(pages, days)

    for i, day in enumerate(days):
        for period in PERIODS:
            page = pages[(day, period)]
            if page is None:
                continue
            # 前後の日：同じ期間のデータがある日へ
            newer = next((d for d in reversed(days[:i]) if pages[(d, period)]), None)
            older = next((d for d in days[i + 1:] if pages[(d, period)]), None)
            nav = {
                "newer": {"date": newer, "href": dated_href(newer, period)} if newer else None,
                "older": {"date": older, "href": dated_href(older, period)} if older else None,
            }
            for is_top in ([False, True] if i == 0 else [False]):
                href = top_href(period) if is_top else dated_href(day, period)
                tabs = {
                    p: ((top_href(p) if is_top else dated_href(day, p)) if pages[(day, p)] else None)
                    for p in PERIODS
                }
                html = day_tpl.render(root=depth_root(href), page=dict(page, tabs=tabs), nav=nav, is_top=is_top)
                _write(out / href / "index.html", html)
    if not days:
        _write(out / "index.html", archive_tpl.render(root="", days=[]))

    # リポジトリの詳しいページ（要約があるものすべて）。言語やスター数は、いちばん新しく見たときの値
    latest_item: dict[str, dict] = {}
    for day in reversed(days):
        for period in ("monthly", "weekly", "daily"):  # 同じ日ならデイリーの値を優先
            page = pages[(day, period)]
            for item in page["cards"] if page else []:
                latest_item[item["repo"]] = item
    for path in sorted((store.dir / "repos").glob("*.json")):
        summary = store.load_summary(path.stem.replace("__", "/", 1))
        if summary is None:
            continue
        repo = summary["repo"]
        _write(out / "r" / repo / "index.html", repo_tpl.render(
            root="../../../", s=summary, item=latest_item.get(repo),
            seen=history.get(repo, {}).get("seen", []),
        ))

    archive_days = [
        dict(pages[(d, "daily")], has_weekly=bool(pages[(d, "weekly")]), has_monthly=bool(pages[(d, "monthly")]))
        for d in days
    ]
    _write(out / "archive" / "index.html", archive_tpl.render(root="../", days=archive_days))
    return out

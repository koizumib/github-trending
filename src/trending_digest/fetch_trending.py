"""github.com/trending（デイリー・全言語）の読み取り。"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from bs4 import BeautifulSoup

from .net import PoliteClient

TRENDING_URL = "https://github.com/trending"


class TrendingError(RuntimeError):
    """Trending のページを取得・読み取りできなかった。黙って0件にせず、これで止める。"""


@dataclass
class TrendingItem:
    rank: int
    repo: str  # owner/name
    description: str
    language: str | None
    stars: int | None
    stars_today: int | None

    def to_dict(self) -> dict:
        return asdict(self)


def fetch_html(client: PoliteClient | None = None) -> str:
    client = client or PoliteClient()
    try:
        resp = client.get(TRENDING_URL)
    except Exception as e:  # noqa: BLE001
        raise TrendingError(f"Trending を取得できなかった: {e}") from e
    if resp.status_code != 200:
        raise TrendingError(f"Trending の取得が HTTP {resp.status_code} で失敗した")
    return resp.text


def _to_int(text: str | None) -> int | None:
    if not text:
        return None
    m = re.search(r"[\d,]+", text)
    return int(m.group().replace(",", "")) if m else None


def parse_trending(html: str) -> list[TrendingItem]:
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("article.Box-row")
    if not rows:
        raise TrendingError("Trending のページに項目が見つからない（ページの構造が変わった可能性）")

    items: list[TrendingItem] = []
    for i, row in enumerate(rows, start=1):
        link = row.select_one("h2 a[href]")
        repo = link["href"].strip("/") if link else ""
        if not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
            raise TrendingError(f"{i}件目のリポジトリ名を読み取れない: {repo!r}")

        desc = row.select_one("p")
        lang = row.select_one('[itemprop="programmingLanguage"]')
        stars = row.select_one(f'a[href="/{repo}/stargazers"]')
        today = row.select_one("span.float-sm-right")
        items.append(
            TrendingItem(
                rank=i,
                repo=repo,
                description=desc.get_text(" ", strip=True) if desc else "",
                language=lang.get_text(strip=True) if lang else None,
                stars=_to_int(stars.get_text() if stars else None),
                stars_today=_to_int(today.get_text() if today else None),
            )
        )
    return items

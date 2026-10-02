import pytest

from github_trending.fetch_trending import TrendingError, parse_trending


def test_parse_saved_page(trending_html):
    items = parse_trending(trending_html)
    assert len(items) == 14
    assert [i.rank for i in items] == list(range(1, 15))

    first = items[0]
    assert first.repo == "debpalash/VoiceStudio"
    assert first.language == "Python"
    assert first.stars == 49558
    assert first.stars_today == 4758
    assert first.description.startswith("VoiceStudio is the open-source")

    assert items[-1].repo == "rakyll/hey"
    assert all("/" in i.repo for i in items)
    assert len({i.repo for i in items}) == len(items)


def test_empty_page_fails_loudly():
    with pytest.raises(TrendingError):
        parse_trending("<html><body>nothing here</body></html>")


def test_broken_repo_link_fails_loudly():
    html = '<article class="Box-row"><h2><a href="/only-owner">x</a></h2></article>'
    with pytest.raises(TrendingError):
        parse_trending(html)

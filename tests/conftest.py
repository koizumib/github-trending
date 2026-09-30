from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def trending_html() -> str:
    return (FIXTURES / "trending.html").read_text(encoding="utf-8")


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    """テストからネットワークに出ない。"""
    import httpx

    def blocked(*args, **kwargs):
        raise RuntimeError("テスト中にネットワークに出ようとした")

    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", blocked)

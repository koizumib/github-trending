"""HTTP の取得。github.com/trending と homepage には1秒以上間を空けて取りに行く。"""

from __future__ import annotations

import time

import httpx

from . import USER_AGENT

MIN_INTERVAL_SEC = 1.0


class PoliteClient:
    """同じクライアントからのリクエストの間を、最低 MIN_INTERVAL_SEC 空ける。"""

    def __init__(self, client: httpx.Client | None = None, min_interval: float = MIN_INTERVAL_SEC):
        self.client = client or httpx.Client(
            headers={"User-Agent": USER_AGENT}, timeout=30.0, follow_redirects=True
        )
        self.min_interval = min_interval
        self._last = 0.0

    def get(self, url: str, **kwargs) -> httpx.Response:
        wait = self._last + self.min_interval - time.monotonic()
        if wait > 0:
            time.sleep(wait)
        try:
            return self.client.get(url, **kwargs)
        finally:
            self._last = time.monotonic()

"""Discord の Webhook に、その日の分を1回だけ送る。

- 先頭のメッセージ：日付、件数、サイトへのリンク
- new（と returning）を1件1つの embed に。タイトルのリンクは詳しいページ
- 1メッセージに embed は10個まで、文字数の合計は 6,000 字まで（Discord の制限）
- continuing は最後のメッセージに名前だけ
- 送った日は data/notified.json に記録し、二度送らない
Webhook の URL は環境変数 DISCORD_WEBHOOK_URL からだけ読む。ログにも出さない。
"""

from __future__ import annotations

import json
import logging
import os
import time

import httpx

from . import USER_AGENT
from .storage import Store, _read, _write

log = logging.getLogger(__name__)

MAX_EMBEDS = 10
MAX_CHARS = 6000
DESC_LIMIT = 350
COLOR_NEW = 0x6D5DFC
COLOR_PENDING = 0x9AA3B8


class NotifyError(RuntimeError):
    pass


def _embed_len(e: dict) -> int:
    return sum(len(e.get(k, "")) for k in ("title", "description")) + len(e.get("footer", {}).get("text", ""))


def build_messages(day: str, store: Store, site_base_url: str) -> list[dict]:
    """送るメッセージ（Webhook に POST する JSON）の一覧を作る。送りはしない。"""
    daily = store.load_daily(day)
    if daily is None:
        raise NotifyError(f"{day} の data/daily/ がない")
    base = site_base_url.rstrip("/") + "/"
    cards = [i for i in daily["items"] if i["status"] in ("new", "returning")]
    continuing = [i for i in daily["items"] if i["status"] == "continuing"]

    embeds = []
    for item in cards:
        s = store.load_summary(item["repo"])
        foot = [x for x in (item.get("language"), f"★ 今日 +{item['stars_today']:,}" if item.get("stars_today") else None) if x]
        if s:
            if s.get("tags"):
                foot.append(" / ".join(s["tags"]))
            desc = s["short"]
            url = f"{base}r/{item['repo']}/"
            color = COLOR_NEW
        else:
            desc = "（まだ要約していません）" + (f"\n{item['description']}" if item.get("description") else "")
            url = f"https://github.com/{item['repo']}"
            color = COLOR_PENDING
        title = f"#{item['rank']} {item['repo']}" + ("（再登場）" if item["status"] == "returning" else "")
        embeds.append({
            "title": title[:256],
            "url": url,
            "description": desc[:DESC_LIMIT],
            "color": color,
            "footer": {"text": "　".join(foot)[:2048]},
        })

    n_new = sum(1 for i in cards if i["status"] == "new")
    header = f"**{day} の GitHub Trending**　新着 {n_new}件／継続 {len(continuing)}件\n{base}"
    messages = [{"content": header, "embeds": []}]
    for e in embeds:
        cur = messages[-1]
        used = len(cur["content"]) + sum(_embed_len(x) for x in cur["embeds"])
        if len(cur["embeds"]) >= MAX_EMBEDS or used + _embed_len(e) > MAX_CHARS:
            cur = {"content": "", "embeds": []}
            messages.append(cur)
        cur["embeds"].append(e)

    if continuing:
        line = "継続：" + ", ".join(i["repo"] for i in continuing)
        last = messages[-1]
        used = len(last["content"]) + sum(_embed_len(x) for x in last["embeds"])
        if len(line) > 1900 or used + len(line) + 1 > MAX_CHARS or len(last["content"]) + len(line) + 1 > 2000:
            messages.append({"content": line[:2000], "embeds": []})
        else:
            last["content"] = (last["content"] + "\n" + line).strip()

    errors = daily.get("errors", [])
    if cards and len(errors) * 2 > len(cards):
        messages.append({"content": f"⚠️ 要約に失敗したものが多い（{len(errors)}件）。data/daily/{day}.json の errors を確かめてください。"})
    return messages


def unsummarized_count(day: str, store: Store) -> int:
    """その日のカード（new / returning）のうち、要約がまだないものの数。"""
    daily = store.load_daily(day) or {"items": []}
    return sum(
        1 for i in daily["items"]
        if i["status"] in ("new", "returning") and store.load_summary(i["repo"]) is None
    )


def alert_message(text: str) -> dict:
    return {"content": f"⚠️ github-trending：{text}"}


def post(messages: list[dict], webhook_url: str, client: httpx.Client | None = None) -> None:
    client = client or httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=30.0)
    for m in messages:
        body = dict(m, allowed_mentions={"parse": []})  # @everyone などを誤って鳴らさない
        for attempt in range(3):
            resp = client.post(webhook_url, json=body)
            if resp.status_code == 429:  # 送りすぎ。言われた秒数だけ待つ
                time.sleep(float(resp.json().get("retry_after", 1)) + 0.5)
                continue
            if resp.status_code >= 400:
                # URL は秘密なので、エラーにも出さない
                raise NotifyError(f"Discord への送信が HTTP {resp.status_code} で失敗した")
            break
        else:
            raise NotifyError("Discord への送信が、待っても通らなかった")
        time.sleep(0.5)


def webhook_url() -> str:
    url = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not url:
        raise NotifyError("環境変数 DISCORD_WEBHOOK_URL がない")
    return url


def already_notified(store: Store, day: str) -> bool:
    return day in _read(store.dir / "notified.json", {"days": []})["days"]


def mark_notified(store: Store, day: str) -> None:
    data = _read(store.dir / "notified.json", {"days": []})
    if day not in data["days"]:
        data["days"] = sorted(data["days"] + [day])
    _write(store.dir / "notified.json", data)


def dump(messages: list[dict]) -> str:
    return json.dumps(messages, ensure_ascii=False, indent=2)

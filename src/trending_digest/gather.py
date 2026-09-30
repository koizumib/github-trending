"""new のリポジトリについて、GitHub API から要約の材料を下集めして .work/ に置く。

判断はしない。取れたものを決まった形で書き出すだけ。足りない分は routine の Claude Code が自分で調べる。
README と依存の定義は raw.githubusercontent.com から取り、API の回数を節約する。
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import httpx

from .net import PoliteClient

log = logging.getLogger(__name__)

API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"

TREE_MAX_DEPTH = 2
TREE_MAX_LINES = 400
README_MAX_BYTES = 60_000
MANIFEST_MAX_BYTES = 20_000
RELEASE_MAX_CHARS = 8_000

# ルートにあれば取る依存の定義
MANIFESTS = [
    "package.json", "pyproject.toml", "setup.py", "setup.cfg", "requirements.txt",
    "Cargo.toml", "go.mod", "Gemfile", "composer.json", "pom.xml",
    "build.gradle", "build.gradle.kts", "CMakeLists.txt", "Package.swift",
    "deno.json", "mix.exs", "pubspec.yaml", "Dockerfile", "docker-compose.yml",
]

META_FIELDS = [
    "full_name", "description", "homepage", "topics", "language", "stargazers_count",
    "forks_count", "created_at", "pushed_at", "default_branch", "archived", "fork",
]


def github_headers() -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


class GatherError(RuntimeError):
    pass


class Gatherer:
    def __init__(self, client: PoliteClient | None = None):
        self.http = client or PoliteClient()
        self.api_headers = github_headers()

    def _api(self, path: str) -> httpx.Response:
        return self.http.get(f"{API}{path}", headers=self.api_headers)

    def _raw(self, repo: str, branch: str, path: str) -> bytes | None:
        resp = self.http.get(f"{RAW}/{repo}/{branch}/{path}")
        return resp.content if resp.status_code == 200 else None

    def gather(self, repo: str, out_dir: Path) -> dict:
        """1件分を集めて out_dir に書き、何が取れたかを返す。"""
        out_dir.mkdir(parents=True, exist_ok=True)
        materials: list[str] = []
        errors: list[str] = []

        # 1. リポジトリの基本情報。これが取れなければ、この1件は諦める
        resp = self._api(f"/repos/{repo}")
        if resp.status_code != 200:
            raise GatherError(f"GET /repos/{repo} が HTTP {resp.status_code}")
        info = resp.json()
        meta = {k: info.get(k) for k in META_FIELDS}
        meta["license"] = (info.get("license") or {}).get("spdx_id")
        branch = info.get("default_branch") or "main"
        _write_json(out_dir / "meta.json", meta)
        materials.append("meta")

        # 2. ファイル構成（深さ2まで）
        paths: list[str] = []
        resp = self._api(f"/repos/{repo}/git/trees/{branch}?recursive=1")
        if resp.status_code == 200:
            tree = resp.json()
            paths = [e["path"] + ("/" if e["type"] == "tree" else "") for e in tree.get("tree", [])]
            shown = [p for p in paths if p.rstrip("/").count("/") < TREE_MAX_DEPTH]
            lines = shown[:TREE_MAX_LINES]
            note = []
            if len(shown) > TREE_MAX_LINES:
                note.append(f"# 深さ{TREE_MAX_DEPTH}までの {len(shown)} 件のうち先頭 {TREE_MAX_LINES} 件")
            if tree.get("truncated"):
                note.append("# GitHub API の結果が途中で切れている（とても大きいリポジトリ）")
            note.append(f"# ファイルとディレクトリの総数：{len(paths)}")
            (out_dir / "tree.txt").write_text("\n".join(note + lines) + "\n", encoding="utf-8")
            materials.append("tree")
        else:
            errors.append(f"tree: HTTP {resp.status_code}")

        root_files = {p for p in paths if "/" not in p}

        # 3. README（ルートにあるもの）
        readme = pick_readme(root_files)
        body = self._raw(repo, branch, readme) if readme else None
        if body is None:
            resp = self._api(f"/repos/{repo}/readme")
            if resp.status_code == 200:
                readme = resp.json().get("path", "README")
                body = self._raw(repo, branch, readme)
        if body is not None:
            _write_text(out_dir / "README.md", body, README_MAX_BYTES)
            materials.append("readme")
        else:
            errors.append("readme: 見つからない")

        # 4. 依存の定義（ルートにあるものだけ）
        for name in MANIFESTS:
            if name not in root_files:
                continue
            body = self._raw(repo, branch, name)
            if body is None:
                errors.append(f"manifest:{name}: 取得できない")
                continue
            _write_text(out_dir / "manifests" / name, body, MANIFEST_MAX_BYTES)
            materials.append(f"manifest:{name}")

        # 5. 最新のリリース
        resp = self._api(f"/repos/{repo}/releases/latest")
        if resp.status_code == 200:
            rel = resp.json()
            text = (
                f"tag: {rel.get('tag_name')}\nname: {rel.get('name')}\n"
                f"published_at: {rel.get('published_at')}\nprerelease: {rel.get('prerelease')}\n\n"
                + (rel.get("body") or "")[:RELEASE_MAX_CHARS]
            )
            (out_dir / "release.md").write_text(text, encoding="utf-8")
            materials.append("release")
        elif resp.status_code != 404:  # 404 はリリースがないだけ
            errors.append(f"release: HTTP {resp.status_code}")

        return {"materials": materials, "errors": errors}


def pick_readme(root_files: set[str]) -> str | None:
    """ルートの README を選ぶ。README.md などの素直な名前を、README-NIX.md のような派生より先にする。"""
    candidates = [p for p in root_files if p.lower().startswith("readme")]
    if not candidates:
        return None
    return min(candidates, key=lambda p: (p.split(".")[0].lower() != "readme", len(p), p))


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, body: bytes, limit: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = body[:limit].decode("utf-8", errors="replace")
    if len(body) > limit:
        text += f"\n\n[… {len(body)} バイトのうち先頭 {limit} バイトだけ保存した]\n"
    path.write_text(text, encoding="utf-8")

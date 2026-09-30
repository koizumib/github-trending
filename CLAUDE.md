# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## このリポジトリについて

trending-digest（仮称）は、**GitHub Trending に新しく上がったリポジトリを毎朝日本語で要約し、静的サイトと Discord 通知で届けるツール**です。

- GitHub Actions で毎朝 7:00（日本時間）に動きます。
- Trending（デイリー・全言語）の25件のうち、ここ10日で初めて上がったものだけを詳しく要約します。続けて上がっているものは名前だけ並べます。
- 要約は README だけでなく、説明文・ファイル構成・依存の定義・examples・リリース・homepage を材料にして、Claude API で作ります。
- 結果は `data/` に JSON でコミットし、そこから HTML を生成して GitHub Pages に公開します。Discord には2〜3行の要約と、詳しいページへのリンクを送ります。

作業の前に `docs/design.md`（設計書）を読んでください。設計判断を変えるときは、`docs/decisions/` にファイルを1つ追加してから実装します。

## 読者

使うのは作者本人（日本のインフラ寄りのエンジニア）だけです。英語を読むのがつらいので、このツールを作っています。要約やサイトの文言は日本語で書きます。専門用語はカタカナにせず英語のままで構いません。

## 大事な原則

1. **行儀よく取得する。** github.com/trending と各 homepage は1日1回、1秒以上間を空けて取りに行きます。User-Agent にこのリポジトリの URL を入れます。リポジトリの情報は、ページを読み取らずに GitHub API で取ります。
2. **1件の失敗で全体を止めない。** 材料集めと要約は1件ずつ try して、失敗したらログに残して次へ進みます。ただし、Trending のページ自体を読み取れないときは、はっきり失敗させて Discord に知らせます（黙って0件にしない）。
3. **要約を盛らない。** README の宣伝文句をそのまま訳しません。分からないことは書かず、推測は推測と書きます。材料が足りなければ `confidence: low` にします。
4. **同じものを二度要約しない。** `data/repos/` に要約があれば使い回します。Claude API は、new のリポジトリに対してだけ呼びます。
5. **秘密情報を出さない。** `ANTHROPIC_API_KEY` と `DISCORD_WEBHOOK_URL` は環境変数（Actions の Secrets）からだけ読みます。コード、ログ、コミット、生成した HTML に出しません。
6. **生成物はコミットしない。** コミットするのは `data/` までです。`site/` は毎回 `data/` から作り直します。
7. **日付は日本時間で扱う。** Actions は UTC で動くので、「今日」は必ず `Asia/Tokyo` で決めます。

## 開発環境

- WSL2（Ubuntu）、Python 3.12。仮想環境は `.venv/` で、実行には `.venv/bin/python` を使います。
- 依存は必要最小限にします（httpx、beautifulsoup4、jinja2、pyyaml、anthropic）。依存を足したら `pyproject.toml` に書きます。
- 手元で動かすときは、秘密情報を `.env` に書きます（`.gitignore` 済み）。Discord への送信は `--dry-run` で止められるようにします。

## よく使うコマンド

```bash
.venv/bin/python -m pytest                              # テスト
.venv/bin/python -m trending_digest run --dry-run       # 取得〜要約〜サイト生成。通知は送らない
.venv/bin/python -m trending_digest build               # data/ から site/ を作り直す
.venv/bin/python -m http.server -d site 8000            # 手元でサイトを見る
```

## テスト

- Trending のページは `tests/fixtures/trending.html` に保存したものを使います。テストからネットワークに出ません。
- GitHub API と Claude API はモックします。要約のプロンプトを変えたときだけ、手元で実際に数件呼んで、本人に結果を見せます。
- 分類（new / continuing / returning）と日付の境目（日本時間の0時前後、10日の境目）は必ずテストします。

## 進め方

- `docs/design.md` の §11 のマイルストーン（M1 → M6）の順に進めます。1つ終わるごとにコミットして、本人に短く報告します。
- コミットのメッセージは日本語で書きます。
- 作者は GitHub Actions に慣れていません。workflow の YAML を書いたり変えたりしたら、何をしているかを平易な日本語で説明してください。

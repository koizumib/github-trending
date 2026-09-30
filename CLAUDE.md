# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## このリポジトリについて

trending-digest（仮称）は、**GitHub Trending に新しく上がったリポジトリを毎朝日本語で要約し、静的サイトと Discord 通知で届けるツール**です。

- 毎朝、Claude Code の routine（クラウドでの定期実行）が動きます。`prepare` スクリプトで Trending を取得・分類し、新しく上がったリポジトリを Claude Code が調べて要約の JSON を書き、push します。
- push をきっかけに GitHub Actions が動き、`data/` から HTML を生成して GitHub Pages に公開し、Discord に通知します。
- Claude API は使いません（契約していません）。要約を書くのは routine の中の Claude Code だけです。

作業の前に `docs/design.md`（設計書）を読んでください。設計判断を変えるときは、`docs/decisions/` にファイルを1つ追加してから実装します。

## 2つの立場

このリポジトリで Claude Code が動く場面は2つあります。どちらの立場かを取り違えないでください。

1. **開発**：本人と一緒にコードを書くとき。このファイルの全体に従います。
2. **毎朝の routine**：要約を書くとき。`docs/routine.md` の手順だけに従います。コードは直しません。手順どおりにできないことがあったら、コードを直さずに、その日のコミットメッセージと `data/daily/` の `errors` に書いて終わります。

## 読者

読むのは作者本人（日本のインフラ寄りのエンジニア）だけです。英語を読むのがつらいので、このツールを作っています。要約やサイトの文言は日本語で書きます。専門用語はカタカナにせず、英語のままで構いません。

## 大事な原則

1. **判断はスクリプトに入れない。** 取得・分類・検査・サイト生成・通知は、入力が同じなら出力も同じになるように書きます。判断が要るのは要約だけで、それは routine の Claude Code がやります。
2. **行儀よく取得する。** github.com/trending と各 homepage は1日1回、1秒以上間を空けて取りに行きます。User-Agent にこのリポジトリの URL を入れます。リポジトリの情報は、ページを読み取らずに GitHub API で取ります。
3. **1件の失敗で全体を止めない。** 1件ずつ処理して、失敗したら記録して次へ進みます。ただし、Trending のページ自体を読み取れないときは、はっきり失敗させて Discord に知らせます（黙って0件にしない）。
4. **要約を盛らない。** README の宣伝文句をそのまま訳しません。分からないことは書かず、推測は推測と書きます。材料が足りなければ `confidence: low` にします。
5. **同じものを二度要約しない。** `data/repos/` に要約があれば使い回します。
6. **秘密情報を出さない。** `DISCORD_WEBHOOK_URL` は環境変数（Actions の Secrets）からだけ読みます。コード、ログ、コミット、生成した HTML に出しません。
7. **生成物はコミットしない。** コミットするのは `data/` までです。`site/` と `.work/` はコミットしません。
8. **日付は日本時間で扱う。** Actions も routine も UTC で動くことがあるので、「今日」は必ず `Asia/Tokyo` で決めます。

## 開発環境

- WSL2（Ubuntu）、Python 3.12。仮想環境は `.venv/` で、実行には `.venv/bin/python` を使います。
- 依存は必要最小限にします（httpx、beautifulsoup4、jinja2、pyyaml、jsonschema）。依存を足したら `pyproject.toml` に書きます。
- 手元で動かすときは、秘密情報を `.env` に書きます（`.gitignore` 済み）。Discord への送信は `--dry-run` で止められるようにします。

## よく使うコマンド

```bash
.venv/bin/python -m pytest                              # テスト
.venv/bin/python -m trending_digest prepare             # 取得・分類・材料の下集め → .work/queue.json
.venv/bin/python -m trending_digest validate            # data/repos/ の形を検査
.venv/bin/python -m trending_digest build               # data/ から site/ を作り直す
.venv/bin/python -m trending_digest notify --dry-run    # 送る内容を表示するだけ
.venv/bin/python -m http.server -d site 8000            # 手元でサイトを見る
```

## テスト

- Trending のページは `tests/fixtures/trending.html` に保存したものを使います。テストからネットワークに出ません。
- GitHub API と Discord はモックします。
- 分類（new / continuing / returning）と日付の境目（日本時間の0時前後、10日の境目）は必ずテストします。

## 進め方

- `docs/design.md` の §11 のマイルストーン（M1 → M7）の順に進めます。1つ終わるごとにコミットして、本人に短く報告します。
- コミットのメッセージは日本語で書きます。
- 作者は GitHub Actions に慣れていません。workflow の YAML を書いたり変えたりしたら、何をしているかを平易な日本語で説明してください。

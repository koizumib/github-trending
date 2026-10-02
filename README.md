# github-trending

GitHub Trending に上がったリポジトリを毎朝日本語で要約し、新聞の形のサイト **「github新聞」** と Discord で届けるツールです。

英語の README を読まなくても、「結局これは何ができるのか」「どう使えそうか」が分かるようにしています。要約には README のほか、ファイル構成・依存の定義・リリースも読み、足りなければ examples やコードまで調べて書いています。

- **サイト**：https://trending-digest.pages.dev/
  - 日次・週次・月次の順位を、1件ずつ短い要約つきで並べます。
  - リポジトリごとに詳しいページがあります（何ができるか、使い方、活用できそうな場面、似ているもの、注意点）。
- **Discord**：毎朝、新しく上がったものの短い要約と、詳しいページへのリンクが届きます。
- **RSS**：https://trending-digest.pages.dev/feed.xml （Atom）。RSS リーダーで購読できます。

要約は Claude Code が書いたもので、誤りを含むことがあります。分からないことは書かず、推測は推測と書くようにしています。

## 仕組み

```
毎朝  GitHub Actions   Trending（日次・週次・月次）を取得して分類し、要約の材料を GitHub API で集める
       ↓ 終わったら API で起動
      Claude Code      材料を読み、足りなければ自分で調べて、日本語の要約を書いて push（routine）
       ↓ push をきっかけに
      GitHub Actions   サイトを作り直して Cloudflare Pages に公開し、Discord に通知する
9:00  GitHub Actions   見張り：取得の失敗や、届いていないことを知らせる
```

- 判断が要る仕事（要約）だけを Claude Code に任せ、ほかは毎回同じ結果になるスクリプトで動かしています。Claude API は使っていません。
- 新しく上がったもの（ここ10日で初めて）だけを要約し、一度書いた要約は使い回します。要約してから90日以上たったものがまた上がったときは、書き直します。
- 記録（`data/`）は JSON でコミットし、HTML は毎回そこから作り直します。

## 文書

| 文書 | 中身 |
|---|---|
| [docs/design.md](docs/design.md) | 設計書。何をどう作っているか、データの形、外で設定したもの |
| [docs/operations.md](docs/operations.md) | 運用の手引き。毎朝の流れ、知らせが来たときの見方、手で動かし直す方法 |
| [docs/routine.md](docs/routine.md) | 毎朝の routine で Claude Code が従う手順（要約の書き方） |
| [docs/decisions/](docs/decisions/README.md) | 設計判断の記録 |
| [CLAUDE.md](CLAUDE.md) | Claude Code で開発するときの決まり |

## 手元で動かす

WSL2（Ubuntu）と Python 3.12 で開発しています。

```bash
python3.12 -m venv .venv && .venv/bin/pip install -e '.[dev]'

.venv/bin/python -m pytest                              # テスト（ネットワークには出ない）
.venv/bin/python -m github_trending build               # data/ から site/ を作る
.venv/bin/python -m http.server -d site 8000            # http://localhost:8000 で見る
.venv/bin/python -m github_trending validate            # 要約の形を検査する
.venv/bin/python -m github_trending notify --dry-run    # Discord に送る内容を表示するだけ
```

`prepare`（Trending の取得と材料集め）は、ふだんは Actions が毎朝動かします。手元で動かすと、github.com と GitHub API に実際に取りに行き、`data/` を書き換えます。
- `--html tests/fixtures/trending.html` を付けると、Trending のページは取りに行きません。ただし、材料集めでは GitHub API を呼びます。
- 試したあとは `git checkout data/` で元に戻します。

Discord に実際に送るときは、`.env` に `DISCORD_WEBHOOK_URL` を書きます（`.gitignore` 済み）。

# trending-digest（仮称）

GitHub Trending に上がったリポジトリを、毎朝日本語で要約して届けるツールです。「結局これは何ができるのか」「どう使えそうか」を、README だけでなくファイル構成や依存、リリースまで読んで、2〜3文の短い要約と詳しいページにまとめます。

- サイト：https://koizumib.github.io/trending-digest/ （デイリー・ウィークリー・マンスリー）
- 通知：毎朝 Discord に、新着の短い要約と詳しいページへのリンクが届く

要約は Claude Code が書いたもので、誤りを含むことがあります。

## 仕組み

```
6:00  GitHub Actions   Trending を取得して分類し、要約の材料を集める
7:00  Claude Code      材料を読み、足りなければ自分で調べて、日本語の要約を書く（routine）
      GitHub Actions   サイトを作り直して GitHub Pages に公開し、Discord に通知する
9:00  GitHub Actions   見張り：届いていなければ知らせる
```

判断が要る仕事（要約）だけを Claude Code に任せ、ほかは毎回同じ結果になるスクリプトで動かしています。Claude API は使っていません。

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

.venv/bin/python -m pytest                              # テスト
.venv/bin/python -m trending_digest build               # data/ から site/ を作る
.venv/bin/python -m http.server -d site 8000            # http://localhost:8000 で見る
.venv/bin/python -m trending_digest validate            # 要約の形を検査する
.venv/bin/python -m trending_digest notify --dry-run    # Discord に送る内容を表示するだけ
```

`prepare`（Trending の取得と材料集め）は、ふだんは Actions が毎朝動かします。手元で動かすと、github.com と GitHub API に実際に取りに行き、`data/` を書き換えます。
- `--html tests/fixtures/trending.html` を付けると、Trending のページは取りに行きません。ただし、材料集めでは GitHub API を呼びます
- 試したあとは `git checkout data/` で元に戻します

Discord に実際に送るときは、`.env` に `DISCORD_WEBHOOK_URL` を書きます（`.gitignore` 済み）。

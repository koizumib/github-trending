# trending-digest 設計書（v0.2 草案）

この文書には、何を作るかとどう作るかを書く。

> v0.2（2026-09-30）：要約を書くのを、Claude API から **Claude Code の routine（クラウドでの定期実行）** に変えた。本人は API を契約しておらず、「Claude Code が定期的に取りに行って要約してくれる」形を想定していたため。README が不親切なときに、Claude Code ならコードや docs を自分で読みに行けるのも利点。

## 1. 目的と範囲

### 作るもの
- 毎朝、GitHub Trending（デイリー・全言語）の25件を取得する
- 過去の記録と比べて、「新しく上がったもの」と「続けて上がっているもの」に分ける
- 新しく上がったものは、Claude Code がリポジトリを調べて日本語の要約を書く
  - 短い要約：2〜3行。通知と一覧に使う
  - 詳しい要約：何ができるか、使い方、向いている人、似ているもの、注意点。詳しいページに使う
- 静的サイトを作って GitHub Pages に公開する
- Discord に通知する

### 作らないもの（v1 では）
- ログインや個人ごとの設定
- 言語や分野による絞り込み（本人は何でも読みたい）
- ウィークリー・マンスリーの Trending（§10 で検討）
- サイト上で質問できる機能（あとで考える）
- Claude API の利用（契約していない）

### 受け入れ基準
- 毎朝、手を動かさなくても Discord に通知が届く
- 通知の各項目をタップすると、そのリポジトリの詳しいページが開く
- 同じリポジトリを2日続けて詳しく要約しない
- README がほとんど空のリポジトリでも、「何をするものか」を一文で言えている。言えないときは「情報が少ない」と正直に書く
- 1件の失敗で全体が止まらない
- Trending のページを読み取れなかったとき、または routine が動かなかったときは、それが分かる

## 2. 役割の分け方

判断が要る仕事は Claude Code に、毎回同じ結果になるべき仕事はスクリプトと Actions に任せる（`docs/decisions/0007-prepare-on-actions.md`）。

| 担当 | やること | 判断の有無 |
|---|---|---|
| GitHub Actions（`prepare.yml`） | Trending の取得、new／continuing の分類、材料の下集め（GitHub API） | なし（決定的） |
| **Claude Code の routine** | 材料を読み、足りなければリポジトリを自分で調べ、要約の JSON を書く | **あり** |
| Python スクリプト（`validate`） | 要約の JSON の形を検査する | なし |
| GitHub Actions（`daily.yml`、`watchdog.yml`） | サイトの生成、Pages への公開、Discord への通知、見張り | なし |

routine（クラウドの実行環境）からは、GitHub API でほかのリポジトリを読めない（割り当てたリポジトリ以外への API 呼び出しは中継に止められる）。そのため材料集めは Actions で行う。

## 3. 全体の流れ

```
 ① GitHub Actions（prepare.yml、毎朝 6:00 ごろ・日本時間）
    ├─ python -m trending_digest prepare
    │     Trending（デイリー・ウィークリー・マンスリー）を取得
    │     → data/daily/、data/weekly/、data/monthly/、history.json を更新
    │     要約する対象について GitHub API で材料を下集め → .work/{owner}__{name}/、.work/queue.json
    ├─ data/ を main に push（[skip ci]：この push では公開も通知もしない）
    ├─ .work/ の中身を work ブランチに上書きで push
    └─ 失敗したら Discord に知らせる
                │
 ② Claude Code の routine（毎朝 7:00 ごろ。クラウドで動く）
    ├─ work ブランチの材料を .work/ に展開（今日の分が来るまで最大30分待つ）
    ├─ queue の1件ずつについて
    │     .work/ の材料を読む → 足りなければ自分で調べる（§5）
    │     → data/repos/{owner}__{name}.json を書く
    ├─ python -m trending_digest validate   （形が崩れていたら直す）
    └─ git commit & push（main）
                │
                ▼ push をきっかけに動く
 ③ GitHub Actions（daily.yml）
    ├─ python -m trending_digest build   data/ → site/
    ├─ actions/deploy-pages で GitHub Pages に公開
    └─ python -m trending_digest notify  Discord に送る（その日の分を1回だけ）

 ④ GitHub Actions（watchdog.yml、毎朝 9:00）
    ├─ 今日の data/daily/ がなければ「取得に失敗した」と Discord に送る
    └─ 今日の分をまだ送っていなければ、要約のあるなしにかかわらず送る
```

- `.work/` は作業場所で、`main` にはコミットしない。`work` ブランチは毎回1コミットだけの状態で上書きする
- データ（`data/`）はコミットする。HTML（`site/`）はコミットせず、毎回 `data/` から作り直す

## 4. データの形

### data/history.json
```json
{
  "owner/name": {
    "first_seen": "2026-09-30",
    "seen": ["2026-09-30", "2026-10-01"]
  }
}
```

### data/daily/YYYY-MM-DD.json
```json
{
  "date": "2026-09-30",
  "items": [
    {"rank": 1, "repo": "owner/name", "status": "new",
     "language": "Rust", "stars": 12345, "stars_today": 890,
     "description": "（Trending のページにある英語の説明）"}
  ]
}
```
`status` は `new`（過去10日に一度も上がっていない）、`continuing`（前の日から続いている）、`returning`（10日より前に上がったことがある）のどれか。

### data/repos/{owner}__{name}.json（Claude Code が書く）
```json
{
  "repo": "owner/name",
  "summarized_at": "2026-09-30",
  "short": "（2〜3行）",
  "what": "何をするものか（一文）",
  "can_do": ["できること"],
  "how_to_use": "導入と最初の一歩",
  "use_cases": ["どう活用できそうか"],
  "for_whom": "向いている人",
  "similar": ["似ている既存のもの（違いも一言）"],
  "tech": "言語・主な依存・動く環境",
  "caveats": "注意点（まだ α 版、ライセンス、要 GPU など）",
  "sources": ["readme", "tree", "manifest:pyproject.toml", "examples/basic.py", "homepage"],
  "confidence": "high | medium | low",
  "confidence_note": "low のときの理由"
}
```
JSON Schema を `schemas/summary.schema.json` に置き、`validate` はこれで検査する。

## 5. 要約の手順（routine の中で Claude Code が従う）

手順は `docs/routine.md` に書き、routine のプロンプトは「`docs/routine.md` に従って今日の分を作って」だけにする。手順を直したいときは、リポジトリのファイルを直せばよい（routine の設定は触らない）。

`prepare` が下集めする材料：

| 材料 | 取り方 |
|---|---|
| 説明文・topics・homepage・ライセンス・作成日・スター数 | `GET /repos/{owner}/{repo}` |
| README | `GET /repos/{owner}/{repo}/readme` |
| ファイル構成（深さ2まで） | `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1` |
| 依存の定義 | ルートの `package.json`、`pyproject.toml`、`Cargo.toml`、`go.mod` など |
| 最新のリリース | `GET /repos/{owner}/{repo}/releases/latest` |

Claude Code が判断して追加で調べるもの：

- README を読んでも「何ができるか」が一文で言えないとき：`examples/`、`docs/`、CLI の入口（`main.go`、`cli.py`、`bin/` など）を読む。必要なら浅く clone する（`git clone --depth 1`、1件あたり 100MB まで）
- homepage が設定されていれば、トップページを読む
- 1件にかける時間の目安は数分。調べても分からなければ `confidence: low` にして次へ進む

書き方の決まり：

- 読者は日本のインフラ寄りのエンジニア。専門用語は英語のままでよいが、「何ができるのか」を最初に書く
- README の宣伝文句（"blazingly fast" など）をそのまま訳さない
- 分からないことは書かない。推測した部分は「〜と思われる」と書く
- 似ているもの（`similar`）は、よく知られたものだけを挙げる

件数：new は1日に多くても25件、ふだんは10件前後の見込み。プランの使用量が心配なら `config.yaml` の `max_summaries_per_day` で上限を決め、超えた分は次の日に回す。

## 6. サイト（GitHub Pages）

```
/                          今日の分（new を順位順にカードで。continuing は下に名前だけ）
/d/2026-09-30/             日ごとのページ
/r/owner/name/             リポジトリの詳しいページ
/archive/                  過去の日の一覧
```

- Python と Jinja2 で HTML を生成する。JavaScript は使わないか、最小限にする
- スマホで読むのが前提。1カラムにし、日本語の長い文章が読みやすいこと（行の長さ、行間）を優先する
- 詳しいページの先頭に「GitHub で開く」リンクと、材料にしたもの（`sources`）、`confidence` を出す
- `confidence: low` のものには「情報が少ない」の印を付ける

## 7. 通知（Discord Webhook）

- 1日1回だけ送る。先頭のメッセージに「2026-09-30 新着 12件／継続 13件」と、サイトへのリンクを入れる
- new を1件1つの embed にする。title はリポジトリ名で、その url を詳しいページにする。description は `short`、footer は言語と今日増えたスター数
- Discord の制限に合わせて分けて送る：1メッセージに embed は10個まで、1メッセージの文字数の合計は 6,000 字まで
- continuing は、最後のメッセージに名前をカンマ区切りで1行だけ入れる
- 同じ日に push が2回あっても二重に送らない（`data/notified.json` に送った日付を記録する）
- 失敗の通知：Trending を読み取れなかったとき、要約の失敗が半分を超えたとき、routine が動いていないとき（§3 の見張り）

## 8. 設定と秘密情報

- `config.yaml`：`new_window_days: 10`、`max_summaries_per_day`、`site_base_url`、`timezone: Asia/Tokyo`
- GitHub の Secrets に登録するもの：`DISCORD_WEBHOOK_URL` だけ
- routine の環境：github.com、api.github.com への通信が必要。homepage を読むなら、任意のサイトに出られるネットワーク設定にする（§10）
- 秘密情報はコードにもログにも出さない

## 9. ディレクトリ構成

```
trending-digest/
  CLAUDE.md
  config.yaml
  pyproject.toml
  docs/
    design.md                 # この文書
    routine.md                # routine の中で Claude Code が従う手順（§5）
    decisions/                # 設計判断の記録。1判断1ファイル
  schemas/
    summary.schema.json
  src/trending_digest/
    cli.py                    # prepare / validate / build / notify
    fetch_trending.py
    classify.py
    gather.py                 # GitHub API から材料を下集めする
    validate.py
    build_site.py
    notify_discord.py
    templates/                # Jinja2
  data/
    history.json
    notified.json
    daily/
    repos/
  tests/
    fixtures/trending.html
  .github/workflows/
    daily.yml                 # data/ への push で build・deploy・notify
    watchdog.yml              # 毎朝 9:00 に今日の分があるか確かめる
    ci.yml                    # テスト
```

## 10. 未決事項（本人が決める・作りながら確かめる）

1. **名前**：仮称は trending-digest
2. **「新しい」の日数**：10日でよいか
3. **returning の扱い**：new として出すか、「再登場」として短く出すか
4. **routine の push 先**：routine が `main` に直接 push できるかを、作るときに確かめる。できなければ、決まったブランチに push し、Actions がそのブランチの push で動くようにする
5. **routine のネットワーク**：homepage を読むために、どこへでも出られる設定にするか。github.com だけに絞るなら、homepage は材料から外す
6. **プランの使用量**：毎日10〜25件を Claude Code で調べて、使用量の上限に当たらないか。最初の1週間ようすを見て `max_summaries_per_day` を決める
7. **ウィークリーの Trending**：**決定**。ウィークリーとマンスリーも毎朝取得してサイトにタブで出す（`docs/decisions/0005-weekly-monthly.md`）
8. **質問できる機能**：詳しいページから質問できるようにするか。入れるなら静的ではなくなる
9. **他のエンジニアにも公開する**：方向は決定。まず1〜2週間は本人だけで使い、よければ公開する（`docs/decisions/0006-public-via-discord.md`）。公開の前に確かめること：アナウンスチャンネルのフォロー先に Webhook の投稿が流れるか、公開前の名前（1）とドメイン、個人のプランの routine で公開の配信を続けてよいか（利用規約）

## 11. マイルストーン

- **M1 取得と記録**：`prepare` の取得・分類・下集め。手元で動かせる。保存した HTML でテストする
- **M2 要約の手順**：`docs/routine.md` と `schemas/summary.schema.json`、`validate` を作る。手元の Claude Code で `docs/routine.md` に従って5件ほど要約させ、本人が読んで質を確かめ、手順を直す
- **M3 サイト**：静的 HTML を生成し、手元のブラウザで見る
- **M4 Actions と Pages**：`daily.yml` で、push をきっかけに build・deploy する
- **M5 Discord**：通知、二重送信の防止、`watchdog.yml`
- **M6 routine**：`/schedule` で毎朝の routine を作る。まず手動で1回動かして確かめる
- **M7 運用して直す**：1〜2週間読んでみて、`docs/routine.md` とページの見た目を直す

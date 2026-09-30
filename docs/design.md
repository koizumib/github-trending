# trending-digest 設計書（v0.3）

この文書には、何を作るかとどう作るかを、**今の実装のとおりに**書く。なぜそうしたかの経緯は `docs/decisions/` にある（一覧は `docs/decisions/README.md`）。毎朝の動かし方と、困ったときの見方は `docs/operations.md` に書く。

- v0.1（2026-09-30）：Actions から Claude API で要約する設計
- v0.2（2026-09-30）：要約を Claude Code の routine に変えた（0002）
- v0.3（2026-09-30）：取得と材料集めを Actions に移した（0007）。ウィークリー・マンスリー（0005）、タグ（0004）、公開先を Cloudflare Pages に（0008）、見た目を新聞のように（0010）

## 1. 目的と範囲

### 作るもの
- 毎朝、GitHub Trending（全言語）のデイリー・ウィークリー・マンスリーを取得する。件数は日によって変わる（おおむね15〜25件）
- デイリーを過去の記録と比べて、「新しく上がったもの（new）」「続けて上がっているもの（continuing）」「久しぶりに戻ってきたもの（returning）」に分ける
- まだ要約のないリポジトリは、Claude Code がリポジトリを調べて日本語の要約を書く
  - 短い要約（`short`）：2〜3文。通知と一覧に使う
  - 詳しい要約：何ができるか、使い方、活用できそうな場面、向いている人、似ているもの、技術、注意点。詳しいページに使う
  - 分野のタグ：決まった語彙から1〜4個
- 静的サイトを作って Cloudflare Pages に公開する
- Discord に通知する

### 作らないもの（今は）
- ログインや個人ごとの設定
- 言語や分野による絞り込み（本人は何でも読みたい）
- サイト上で質問できる機能（§10）
- Claude API の利用（契約していない）

### 受け入れ基準
- 毎朝、手を動かさなくても Discord に通知が届く
- 通知の各項目をタップすると、そのリポジトリの詳しいページが開く
- 同じリポジトリを二度要約しない
- README がほとんど空のリポジトリでも、「何をするものか」を一文で言えている。言えないときは「情報が少ない」と正直に書く
- 1件の失敗で全体が止まらない
- Trending を読み取れなかったとき、または routine が終わらなかったときは、それが Discord で分かる

## 2. 役割の分け方

判断が要る仕事は Claude Code に、毎回同じ結果になるべき仕事はスクリプトと GitHub Actions に任せる。

| 担当 | やること | 判断の有無 |
|---|---|---|
| GitHub Actions（`prepare.yml`） | Trending の取得、分類、材料の下集め（GitHub API） | なし（決定的） |
| **Claude Code の routine** | 材料を読み、足りなければ自分で調べ、要約の JSON を書く | **あり** |
| Python（`validate`） | 要約の JSON の形を検査する | なし |
| GitHub Actions（`daily.yml`） | サイトの生成、Cloudflare Pages への公開、Discord への通知 | なし |
| GitHub Actions（`watchdog.yml`） | 取得の失敗を知らせる。未送信なら送る | なし |

routine（Claude Code のクラウドの実行環境）からは、GitHub API でほかのリポジトリを読めない。GitHub への通信が専用の中継を通り、routine に割り当てたリポジトリ以外への API 呼び出しは止められるため。そこで材料集めは Actions で行う（0007）。

## 3. 全体の流れ

```
 ① GitHub Actions「取得と材料集め」（prepare.yml、毎朝 6:00 ごろ・日本時間）
    ├─ python -m trending_digest prepare
    │     Trending（デイリー・ウィークリー・マンスリー）を取得
    │     → data/daily/、data/weekly/、data/monthly/、data/history.json を更新
    │     要約のないものについて GitHub API で材料を集める → .work/{owner}__{name}/、.work/queue.json
    ├─ data/ を main に push（[skip ci] 付き：この push では公開も通知もしない）
    ├─ .work/ の中身を work ブランチに上書きで push
    └─ 失敗したら Discord に知らせる
                │
 ② Claude Code の routine（毎朝 7:08 ごろ。Anthropic のクラウドで動く）
    ├─ work ブランチの材料を .work/ に展開（今日の分が来るまで最大30分待つ）
    ├─ queue の1件ずつ：材料を読む → 足りなければ自分で調べる → data/repos/{owner}__{name}.json を書く
    ├─ python -m trending_digest validate
    └─ main に commit & push
                │
                ▼ push をきっかけに動く
 ③ GitHub Actions「サイトを作って公開する」（daily.yml）
    ├─ validate → build（data/ → site/）→ Cloudflare Pages に公開（移行中は GitHub Pages にも）
    └─ notify：その日の分を Discord に1回だけ送り、data/notified.json に記録（[skip ci]）

 ④ GitHub Actions「見張り」（watchdog.yml、毎朝 9:00）
    ├─ 今日の data/daily/ がなければ「取得できていない」と Discord に送る
    └─ 今日の分をまだ送っていなければ、要約のあるなしにかかわらず送る
```

- `.work/` は作業場所で、`main` にはコミットしない。`work` ブランチは毎回1コミットだけの状態で上書きする
- `data/` はコミットする。HTML（`site/`）はコミットせず、毎回 `data/` から作り直す。見た目を変えれば過去の日もまとめて作り直せる
- routine が要約を1件も書かない日（対象が0件、または失敗）は push がないので、通知は ④ が送る

## 4. データの形

### data/history.json（デイリーに上がった日の記録）
```json
{
  "owner/name": {"first_seen": "2026-09-30", "seen": ["2026-09-30", "2026-10-01"]}
}
```

### data/daily/YYYY-MM-DD.json（その日のデイリーの順位）
```json
{
  "date": "2026-09-30",
  "items": [
    {"rank": 1, "repo": "owner/name", "status": "new",
     "language": "Rust", "stars": 12345, "stars_today": 890,
     "description": "（Trending のページにある英語の説明）"}
  ],
  "errors": [{"repo": "owner/name", "reason": "要約できなかった理由"}]
}
```
- `status`：`new`（前日から10日前までに一度も上がっていない）、`continuing`（その期間に上がっている）、`returning`（記録はあるが最後が10日より前）。分類には今日より前の記録だけを使う（0001）
- `errors`：routine が要約できなかったもの。`prepare` が書き直しても消えない

### data/weekly/YYYY-MM-DD.json、data/monthly/YYYY-MM-DD.json（その日に見た週・月の Trending）
```json
{"date": "2026-09-30", "period": "weekly",
 "items": [{"rank": 1, "repo": "owner/name", "language": "Go", "stars": 100,
            "stars_period": 900, "description": "…"}]}
```
- 分類はしない。`stars_period` はその期間に増えたスター数

### data/repos/{owner}__{name}.json（要約。routine が書く）
```json
{
  "repo": "owner/name",
  "summarized_at": "2026-09-30",
  "short": "2〜3文、150字くらいまで",
  "what": "何をするものか（一文。種類が分かるように）",
  "can_do": ["できること"],
  "how_to_use": "導入と最初の一歩",
  "use_cases": ["どう活用できそうか（推測なので「〜に使えそう」）"],
  "for_whom": "向いている人",
  "similar": ["よく知られた似ているもの：違い"],
  "tech": "言語・主な依存・動く環境",
  "caveats": "注意点",
  "tags": ["決まった語彙から1〜4個。先頭が主な分野"],
  "sources": ["meta", "readme", "tree", "manifest:pyproject.toml", "release", "examples/basic.py"],
  "confidence": "high | medium | low",
  "confidence_note": "medium・low のときの理由"
}
```
- 形は `schemas/summary.schema.json` で決める。タグの語彙の正本もここ（0004）。`validate` がこれで検査する

### data/notified.json（Discord に送った日）
```json
{"days": ["2026-09-30"]}
```

### work ブランチ（毎回上書き。main には入れない）
```
queue.json                       # {"date", "items": [...], "deferred": [...]}
{owner}__{name}/meta.json        # 説明文、topics、homepage、ライセンス、作成日、スター数、size
{owner}__{name}/README.md        # 大きければ先頭 60KB
{owner}__{name}/tree.txt         # 深さ2まで、最大400行
{owner}__{name}/manifests/…      # ルートの依存の定義
{owner}__{name}/release.md       # 最新のリリース
```
- `queue.json` の `items` の順番：デイリーの new → returning → 前の日に回された continuing → ウィークリー → マンスリー（その中は順位順）。同じリポジトリは1回だけ。`config.yaml` の `max_summaries_per_day` を超えた分は `deferred` に入り、次の日に回る

## 5. 要約の手順

routine が従う手順は `docs/routine.md` に書く。routine のプロンプトは「`docs/routine.md` に従って」とだけ書き、手順を直したいときはこのファイルを直す（routine の設定は触らない）。

- 1件ずつ、材料を読む → 足りなければ自分で調べる（examples、docs、CLI の入口、homepage）→ 書く
- `confidence` が `high` にならないと思ったら、書く前に必ず追加で調べる
- 読者は日本のインフラ寄りのエンジニア。専門用語は英語のまま。「何ができるのか」を最初に書く
- 盛らない。README の宣伝文句を訳さない。分からないことは書かない。推測は推測と書く
- 似ているもの（`similar`）は、よく知られたものだけ

## 6. サイト（Cloudflare Pages）

公開先：https://trending-digest.pages.dev/ （移行中は https://koizumib.github.io/trending-digest/ にも同じものを出している。0008）

```
/                          最新の日のデイリー
/weekly/  /monthly/        最新の日のウィークリー・マンスリー
/d/2026-09-30/             日ごとのページ（/d/日付/weekly/、/d/日付/monthly/ も）
/r/owner/name/             リポジトリの詳しいページ
/archive/                  過去の日の一覧
```

- Python と Jinja2 で HTML を生成する。入力が同じなら出力も同じ（生成時刻などは入れない）
- 上部のタブでデイリー・ウィークリー・マンスリーを切り替える。データのない期間のタブは押せない
- デイリーは new と returning をカードで、continuing は下に名前と一文だけ並べる。ウィークリー・マンスリーは全件カード
- カードの下にタグ。要約のないものは「まだ要約していません」と英語の説明を出す
- 詳しいページの先頭に「GitHub で開く」、タグ、確かさ（`confidence`）。`low` には「情報が少ない」の印。末尾に材料（`sources`）と、Trending に上がった日
- 見た目は新聞のように（0010）：見出しと本文は明朝体、順位やタグなどは小さなゴシック体。一覧のページの頭に大きな日付の題字と二重の罫線。1位はトップ記事として大きく。記事は箱に入れず罫線で区切る。スマホは1カラム、PC（幅 900px 以上）は2段組みで段のあいだに縦の罫線。詳しいページは1カラム
- 右上のボタンでダーク／ライトを切り替える（初めは OS の設定、選んだものはブラウザに覚える）。JavaScript はこのためだけの数行（0003）

## 7. 通知（Discord Webhook）

- その日のデイリーを1日1回だけ送る。送った日は `data/notified.json` に記録する
- 先頭のメッセージ：「**2026-09-30 の GitHub Trending**　新着 12件／継続 13件」とサイトへのリンク
- new と returning を1件1つの embed に。title は「#順位 owner/name」で、リンクは詳しいページ（要約がなければ GitHub）。description は `short`、footer は言語・今日増えたスター・タグ
- 1メッセージに embed は10個まで、文字数の合計は 6,000 字まで（Discord の制限）に合わせて分けて送る
- continuing は最後のメッセージに名前をカンマ区切りで1行
- `@everyone` などは鳴らさない（`allowed_mentions` を空にする）
- 知らせるもの：
  - 取得と材料集めが失敗したとき（`prepare.yml` から）
  - 9時の時点で今日の分を取得できていないとき（`watchdog.yml`）
  - 9時の時点でまだ送っていないとき：要約が足りない件数を先頭に書いて送る（`watchdog.yml`）
  - 要約の失敗（`errors`）がカードの半分を超えたとき（通知の最後に書く）

## 8. 設定と、外で設定したもの

### config.yaml
| キー | 値 | 意味 |
|---|---|---|
| `new_window_days` | 10 | 何日以内に上がっていなければ new とみなすか |
| `max_summaries_per_day` | 15 | 1日に要約する件数の上限 |
| `site_base_url` | https://trending-digest.pages.dev/ | 通知に入れるリンクの元 |
| `timezone` | Asia/Tokyo | 「今日」を決めるタイムゾーン |

### GitHub（リポジトリ koizumib/trending-digest、公開）
- Secrets：`DISCORD_WEBHOOK_URL`、`CLOUDFLARE_API_TOKEN`（Cloudflare Pages の編集権限だけ）、`CLOUDFLARE_ACCOUNT_ID`。GitHub API の鍵は Actions が自動で用意する `GITHUB_TOKEN` を使う
- Pages：Source は「GitHub Actions」（Cloudflare Pages への移行が終わったら外す）

### Cloudflare
- Pages のプロジェクト `trending-digest`（Direct Upload。GitHub にはつながない）。`daily.yml` が `wrangler pages deploy` で送る
- Access での制限はかけない
- ブランチ：`main`（コードと data/）、`work`（材料。毎朝上書き）

### Claude Code の routine
| 項目 | 値 |
|---|---|
| 名前 | trending-digest 毎朝の要約（`trig_01VBSyXRh8g9UMrCLPSrneVQ`） |
| 時刻 | cron `0 22 * * *`（UTC）＝ 毎朝 7:00 日本時間（実際は数分ずれる） |
| 実行環境 | 「github trending」（クラウド、ネットワークは Full） |
| モデル | claude-sonnet-5-5 |
| ツール | Bash、Read、Write、Edit、Glob、Grep、WebFetch |
| 管理画面 | https://claude.ai/code/routines/trig_01VBSyXRh8g9UMrCLPSrneVQ |

- routine の GitHub への push は、Claude のアカウントにつないだ GitHub の権限で行う
- クラウドの実行環境は Ubuntu。`python3` が 3.11 のことがあるので `python3.12` を使う。clone 直後は detached HEAD なので `git push origin HEAD:main` で push する

### 秘密情報
- `DISCORD_WEBHOOK_URL` は環境変数（Actions の Secrets、手元では `.env`）からだけ読む。コード、ログ、コミット、HTML に出さない。送信のエラーにも URL を出さない

## 9. ディレクトリ構成

```
trending-digest/
  README.md                   # 入口
  CLAUDE.md                   # Claude Code 向けの決まり
  config.yaml
  pyproject.toml
  docs/
    design.md                 # この文書
    routine.md                # routine の中で Claude Code が従う手順
    operations.md             # 毎朝の動き、困ったときの見方と直し方
    decisions/                # 設計判断の記録（1判断1ファイル。README.md が一覧）
  schemas/
    summary.schema.json       # 要約の形とタグの語彙
  src/trending_digest/
    cli.py                    # prepare / validate / build / notify / watchdog / alert
    config.py                 # config.yaml、日本時間の「今日」、.env
    net.py                    # 1秒以上空けて取りに行く HTTP クライアント
    fetch_trending.py         # Trending のページの読み取り
    classify.py               # new / continuing / returning
    gather.py                 # GitHub API から材料を集める
    pipeline.py               # 記録と、要約の対象（queue）を決める
    storage.py                # data/ の読み書き
    validate.py
    build_site.py
    notify_discord.py
    templates/  static/       # Jinja2 のテンプレートと CSS
  data/
    history.json  notified.json
    daily/  weekly/  monthly/  repos/
  tests/
    fixtures/trending*.html   # 保存しておいた Trending のページ（デイリー・ウィークリー・マンスリー）
  .github/workflows/
    prepare.yml               # 6:00 取得と材料集め
    daily.yml                 # data/ などへの push で build・Cloudflare Pages へ公開・notify
    watchdog.yml              # 9:00 見張り
    ci.yml                    # テスト
```

## 10. 未決事項

1. **名前**：仮称は trending-digest。公開するなら決める
2. **「新しい」の日数**：10日でよいか
3. **returning の扱い**：今は new と同じくカードで出し、「再登場」の印を付けている。これでよいか
4. **プランの使用量**：毎日15件前後を routine で調べて、使用量の上限に当たらないか。最初の1〜2週間ようすを見て `max_summaries_per_day` を決める
5. **質問できる機能**：詳しいページから質問できるようにするか。入れるなら静的ではなくなる
6. **他のエンジニアにも公開する**：方向は決定。まず1〜2週間は本人だけで使い、よければ公開する（0006）。公開の前に確かめること：アナウンスチャンネルのフォロー先に Webhook の投稿が流れるか、名前とドメイン、個人のプランの routine で公開の配信を続けてよいか（利用規約）
7. **過去の Trending**：記録を始めた 2026-09-30 より前の分は、Wayback Machine の保存ページから取れる可能性がある。やるなら、何日分残っているかを先に確かめる

## 11. マイルストーン

| | 内容 | 状態 |
|---|---|---|
| M1 | 取得と記録（`prepare`、保存した HTML でのテスト） | 済み |
| M2 | 要約の手順（`docs/routine.md`、Schema、`validate`）、試しに要約 | 済み |
| M3 | サイト | 済み |
| M4 | Actions と Pages | 済み |
| M5 | Discord の通知と見張り | 済み |
| M6 | routine（毎朝の定期実行）と、取得の Actions への移動 | 済み（2026-09-30） |
| M7 | 1〜2週間運用して、`docs/routine.md` とページの見た目を直す | 2026-10-01 から |

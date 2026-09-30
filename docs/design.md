# trending-digest 設計書（v0.1 草案）

この文書には、何を作るかとどう作るかを書く。

## 1. 目的と範囲

### 作るもの
- 毎朝、GitHub Trending（デイリー・全言語）の25件を取得する
- 過去の記録と比べて、「新しく上がったもの」と「続けて上がっているもの」に分ける
- 新しく上がったものは、複数の材料から日本語の要約を作る
  - 短い要約：2〜3行。通知と一覧に使う
  - 詳しい要約：何ができるか、使い方、向いている人、似ているもの、注意点。詳しいページに使う
- 静的サイトを作って GitHub Pages に公開する
- Discord に通知する

### 作らないもの（v1 では）
- ログインや個人ごとの設定
- 言語や分野による絞り込み（本人は何でも読みたい）
- ウィークリー・マンスリーの Trending（§10 で検討）
- サイト上で質問できる機能（あとで考える）

### 受け入れ基準
- 毎朝 7:00 ごろ（日本時間）に、手を動かさなくても Discord に通知が届く
- 通知の各項目をタップすると、そのリポジトリの詳しいページが開く
- 同じリポジトリを2日続けて詳しく要約しない
- README がほとんど空のリポジトリでも、「何をするものか」を一文で言えている。言えないときは「情報が少ない」と正直に書く
- 1件の失敗（API のエラー、要約の失敗）で全体が止まらない
- Trending のページの構造が変わって読み取れなくなったら、それを Discord に知らせる

## 2. 全体の流れ

```
 GitHub Actions（毎日 UTC 22:00 = 日本時間 7:00）
   │
   ├─ 1. fetch    github.com/trending を1回だけ取得 → 25件の owner/name
   ├─ 2. classify data/history.json と比べる
   │                ├─ new        ：過去10日に一度も上がっていない
   │                ├─ continuing ：前の日から続いている
   │                └─ returning  ：10日より前に上がったことがある（要約のキャッシュがあれば使い回す）
   ├─ 3. gather   new のものだけ、GitHub API などで材料を集める（§4）
   ├─ 4. summarize Claude API で要約する → data/repos/{owner}__{name}.json
   ├─ 5. record   data/daily/YYYY-MM-DD.json と history.json を更新してコミット・プッシュ
   ├─ 6. build    data/ から site/ に静的 HTML を生成
   ├─ 7. deploy   actions/deploy-pages で GitHub Pages に公開
   └─ 8. notify   Discord Webhook に送る
```

データ（`data/`）はリポジトリにコミットする。生成した HTML（`site/`）はコミットせず、毎回 `data/` から作り直す。サイトの見た目を変えたくなったら、過去の日の分もまとめて作り直せる。

## 3. データの形

### data/history.json
リポジトリごとに、Trending に上がった日の一覧を持つ。

```json
{
  "owner/name": {
    "first_seen": "2026-09-30",
    "seen": ["2026-09-30", "2026-10-01"]
  }
}
```

### data/daily/YYYY-MM-DD.json
その日の Trending の順位のスナップショット。

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

### data/repos/{owner}__{name}.json
要約。一度作ったら使い回す。`returning` のものは、要約してから90日以上経っていたら作り直す（§10）。

```json
{
  "repo": "owner/name",
  "summarized_at": "2026-09-30",
  "model": "claude-sonnet-5-5",
  "sources": ["readme", "homepage", "tree", "manifest:pyproject.toml", "release"],
  "short": "（2〜3行）",
  "what": "何をするものか（一文）",
  "can_do": ["できること", "..."],
  "how_to_use": "導入と最初の一歩",
  "use_cases": ["どう活用できそうか", "..."],
  "for_whom": "向いている人",
  "similar": ["似ている既存のもの（違いも一言）"],
  "tech": "言語・主な依存・動く環境",
  "caveats": "注意点（まだ α 版、ライセンス、要 GPU など）",
  "confidence": "high | medium | low",
  "confidence_note": "low のときの理由（README がほぼ空、など）"
}
```

## 4. 要約の材料（README だけに頼らない）

1件ごとに次を集める。取れないものは飛ばす。合計がおよそ 30,000 トークンを超えそうなら、下のものから削る。

| 材料 | 取り方 | 分かること |
|---|---|---|
| 説明文・topics・homepage・ライセンス・作成日・スター数 | `GET /repos/{owner}/{repo}` | 作者自身の一言での説明、分野 |
| README | `GET /repos/{owner}/{repo}/readme`（raw） | 基本の説明 |
| ファイル構成 | `GET /repos/{owner}/{repo}/git/trees/{branch}?recursive=1` を深さ2までに絞る | CLI かライブラリかアプリか、規模 |
| 依存の定義 | `package.json`、`pyproject.toml`、`Cargo.toml`、`go.mod` など、ルートにあるものだけ | 何の上に作られているか、種類 |
| examples・docs | `examples/`、`docs/` の一覧と、先頭の1〜2ファイル | 実際の使い方 |
| 最新のリリース | `GET /repos/{owner}/{repo}/releases/latest` | 成熟度、最近の変化 |
| homepage | 設定されていればトップページを1つだけ取得し、本文のテキストだけ抜き出す（最大 20KB） | README にない説明 |

- API は Actions の `GITHUB_TOKEN` で呼ぶ（1時間あたり1,000回まで。1日に使うのは多くても200回程度）
- github.com/trending と homepage には、分かる User-Agent を付け、1秒以上間を空けて取りに行く
- README に画像しかない、中国語だけ、などの場合もある。材料の言語は問わず、要約は日本語で書かせる

## 5. 要約（Claude API）

- **呼び方**：tool use（構造化出力）で、§3 の JSON の形で必ず返させる。形が崩れたら1回だけやり直し、それでも駄目なら `confidence: low` として短い要約だけを残す
- **モデル**：設定ファイルで変えられるようにする。最初は `claude-sonnet-5-5`、費用を抑えたければ `claude-haiku-4-5` を試す（§10）
- **システムプロンプトの方針**
  - 読者は日本のインフラ寄りのエンジニア。専門用語はそのままでよいが、「何ができるのか」を最初に書く
  - 誇張しない。README の宣伝文句（"blazingly fast" など）をそのまま訳さない
  - 分からないことは書かない。推測した部分は「〜と思われる」と書く
  - 似ているもの（`similar`）は、よく知られたものだけを挙げる。自信がなければ空でよい
- **件数と費用**：new は1日に多くても25件、ふだんは10件前後の見込み。上限を設定（`max_summaries_per_day`）で決め、超えた分は次の日に回す

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
- 失敗の通知：Trending を読み取れなかった場合と、要約の失敗が半分を超えた場合は、その旨を送る

## 8. 設定と秘密情報

- `config.yaml`：`new_window_days: 10`、`model`、`max_summaries_per_day`、`site_base_url`、`timezone: Asia/Tokyo`
- リポジトリの Secrets に登録するもの：`ANTHROPIC_API_KEY`、`DISCORD_WEBHOOK_URL`
- 秘密情報はコードにもログにも出さない

## 9. ディレクトリ構成

```
trending-digest/
  CLAUDE.md
  config.yaml
  pyproject.toml
  docs/
    design.md                 # この文書
    decisions/                # 設計判断の記録。1判断1ファイル
  src/trending_digest/
    cli.py                    # python -m trending_digest run / build / notify
    fetch_trending.py         # Trending のページの読み取り
    classify.py
    gather.py                 # GitHub API・homepage から材料を集める
    summarize.py              # Claude API
    build_site.py
    notify_discord.py
    templates/                # Jinja2
  data/
    history.json
    daily/
    repos/
  tests/
    fixtures/trending.html    # 保存しておいた Trending のページ
  .github/workflows/
    daily.yml                 # 定期実行
    ci.yml                    # push 時のテスト
```

## 10. 未決事項（本人が決める）

1. **名前**：仮称は trending-digest
2. **「新しい」の日数**：10日でよいか。長いほど通知は減るが、「前に見たけど忘れた」ものも出てこなくなる
3. **returning の扱い**：10日より前に上がっていたものが戻ってきたとき、new として出すか、「再登場」として短く出すか
4. **要約のモデル**：Sonnet で質を取るか、Haiku で費用を抑えるか。最初の1週間は両方で作って比べてもよい
5. **ウィークリーの Trending**：週に1回、ウィークリーのまとめも作るか
6. **質問できる機能**：詳しいページから Claude に質問できるようにするか。入れるなら静的ではなくなる（Cloudflare Workers などが要る）

## 11. マイルストーン

- **M1 取得と記録**：Trending を読み取って `data/daily` と `history.json` に書く。手元で動かせる。保存した HTML でテストする
- **M2 材料集めと要約**：new のものについて §4 の材料を集め、要約の JSON を作る。まず手元で5件ほど作り、本人が読んで質を確かめる
- **M3 サイト**：静的 HTML を生成し、手元のブラウザで見る
- **M4 Actions と Pages**：毎朝の定期実行と Pages への公開。まず手動実行（`workflow_dispatch`）で確かめてから cron を有効にする
- **M5 Discord**：通知と、失敗の通知
- **M6 運用して直す**：1〜2週間読んでみて、要約のプロンプトとページの見た目を直す

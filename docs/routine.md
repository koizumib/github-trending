# 毎朝の routine の手順

この文書は、毎朝の routine で動く Claude Code が従う手順です。あなたの仕事は、**今日 Trending に新しく上がったリポジトリを調べて、日本語の要約の JSON を書き、push すること**です。

## 守ること

- **コードは直さない。** `src/`、`tests/`、`schemas/`、`docs/`、`config.yaml`、`.github/` は触りません。手順どおりにできないことがあっても、コードを直して切り抜けようとせず、下の「うまくいかないとき」に従います。
- **書いてよいのは次の2つだけ**：`data/repos/{owner}__{name}.json`（要約）と、今日の `data/daily/YYYY-MM-DD.json` の `errors`。`history.json`、`daily` の `items`、`weekly/`、`monthly/` は Actions の `prepare` が書くので、手で変えません。
- **`.work/` と `site/` はコミットしない。**
- **行儀よく取得する。** homepage は1件につきトップページを1回だけ取りに行きます。同じサイトに続けて取りに行くときは1秒以上間を空けます。

## 1. 準備

Trending の取得と材料集め（`prepare`）は、毎朝 6:00 ごろに GitHub Actions が済ませています。結果は次の2か所にあります。

- `main` の `data/`：今日の `data/daily/YYYY-MM-DD.json`、`weekly/`、`monthly/`、`history.json`
- `work` ブランチ：要約する対象の材料と、その一覧 `queue.json`

あなたは `prepare` を動かしません（クラウドの環境からは GitHub API でほかのリポジトリを読めないため）。次のコマンドで準備します。

```bash
test -x .venv/bin/python || (python3.12 -m venv .venv && .venv/bin/pip install -q -e .)
git pull -q origin main
TODAY=$(TZ=Asia/Tokyo date +%F); echo "今日は $TODAY"
git fetch -q origin work && rm -rf .work && mkdir .work && git archive origin/work | tar -x -C .work
python3 -c "import json;print(json.load(open('.work/queue.json'))['date'])"
```

- このツールは Python 3.12 以上が要ります。クラウドの環境では `python3` が 3.11 のことがあるので、必ず `python3.12` で `.venv` を作ります。`python3.12` がなければ `python3.13` を使います。
- `.work/` は `.gitignore` 済みです。`git archive` で展開するだけなので、`main` の作業ツリーにもインデックスにも入りません。
- **最後の行の日付が `$TODAY` と違うとき、または `work` ブランチがないとき**は、Actions の取得がまだ終わっていません。5分待ってから `git fetch` からやり直します。これを6回（30分）繰り返しても今日の日付にならなければ、要約はせず、何もコミットせずに報告して終わります。朝9時の見張り（watchdog）が Discord に知らせます。
- `queue.json` の `items` が空なら、今日は要約するものがありません。何もコミットせずに、そう報告して終わります（通知は9時の見張りが送ります）。

## 2. 1件ずつ要約する

`.work/queue.json` の `items` を上から順に1件ずつ処理します。`deferred` にあるものは今日はやりません（次の日に回ります）。

各項目には次のものがあります。

| キー | 中身 |
|---|---|
| `repo` | `owner/name` |
| `status` | なぜ対象になったか。`new`（今日デイリーに初めて上がった）、`returning`（久しぶりに上がった）、`continuing`（前の日に回されたもの）、`weekly` / `monthly`（ウィークリー・マンスリーにだけ出ていて、まだ要約がない）。書き方は変わらない |
| `work_dir` | 材料の置き場所（下の表） |
| `output` | 書き出す先（`data/repos/{owner}__{name}.json`） |
| `materials` | 集められた材料の名前 |
| `errors` | 集められなかったもの |

`work_dir` の中身：

| ファイル | 中身 |
|---|---|
| `meta.json` | 説明文、topics、homepage、ライセンス、作成日、最終 push、スター数、`size`（KB） |
| `README.md` | ルートの README（大きければ先頭 60KB） |
| `tree.txt` | ファイル構成（深さ2まで） |
| `manifests/` | ルートにある依存の定義（`package.json`、`pyproject.toml`、`Cargo.toml`、`go.mod` など） |
| `release.md` | 最新のリリース（なければファイルもない） |

### 2-1. 材料を読む

まず `meta.json` → `README.md` → `tree.txt` → `manifests/` → `release.md` の順に読みます。README に画像しかない、中国語だけ、などもあります。材料の言語は問いません。

### 2-2. 足りなければ自分で調べる

材料を読んでも「**これは何をするものか**」を一文で言えないときや、使い方が分からないときは、次の順で調べます。

1. `examples/`、`docs/`、CLI の入口（`main.go`、`cmd/`、`cli.py`、`__main__.py`、`bin/`、`src/main.rs` など）を読みます。1ファイルだけなら `https://raw.githubusercontent.com/{owner}/{name}/{default_branch}/{path}` で読みます。
2. たくさん読む必要があれば、浅く clone します。ただし、クラウドの環境では、ほかのリポジトリの clone は止められることがあります。失敗したら clone はあきらめ、1 の方法で必要なファイルだけを読みます。`meta.json` の `size` が 100000（KB、約 100MB）を超えるものは clone しません。
   ```bash
   git clone --depth 1 --quiet https://github.com/{owner}/{name}.git .work/clone/{owner}__{name}
   ```
3. `meta.json` に `homepage` があり、README だけでは分からないときは、そのトップページを1回だけ読みます。

1件にかける時間の目安は数分です。調べても分からなければ、分かった範囲で書いて `confidence: low` にし、次へ進みます。

### 2-3. 要約の JSON を書く

`output` のパスに、次の形で書きます。形は `schemas/summary.schema.json` で決まっていて、キーは全部必須です。書くことがないときは、空の文字列 `""` か空の配列 `[]` にします。

| キー | 書くこと |
|---|---|
| `repo` | `owner/name`（queue のとおり） |
| `summarized_at` | 今日の日付（`queue.json` の `date`） |
| `short` | 2〜3文、全体で150字くらいまで。一覧と Discord の通知に出ます。**最初の文で「何をするものか」を言います**。そのあと、特徴を1つか、誰にとって嬉しいかを書きます |
| `what` | 何をするものかの一文。「〜する CLI」「〜のための Python ライブラリ」「〜を動かすセルフホストの Web アプリ」のように、**種類**が分かるようにします |
| `can_do` | できることの箇条書き（3〜6個）。具体的な機能を書きます |
| `how_to_use` | 導入と最初の一歩。インストールのコマンドや、最初に打つコマンドが README にあれば、それを短く書きます |
| `use_cases` | どう活用できそうか（2〜4個）。読者（下記）の仕事の場面に引きつけて書きます。**ここは推測なので、「〜に使えそう」と書きます** |
| `for_whom` | 向いている人 |
| `similar` | 似ている既存のもの。よく知られたものだけを挙げ、違いを一言添えます（例：`"ab（Apache Bench）：用途はほぼ同じ。こちらは Go 製で1ファイル"`）。自信がなければ `[]` |
| `tech` | 言語、主な依存（manifests から）、動く環境（OS、GPU の要否、Docker など） |
| `caveats` | 注意点。まだ α 版、作られて間もない、長く更新されていない、ライセンスが制限的または不明、GPU が要る、外部の有料 API が要る、アーカイブ済み、など。材料から分かることだけを書きます |
| `tags` | 分野を下の一覧から1〜4個選ぶ。**先頭に主な分野**を置く。一覧にない言葉は使わない（形の検査で落ちる） |
| `sources` | 実際に読んだもの。`meta`、`readme`、`tree`、`manifest:{ファイル名}`、`release`、`homepage`、読んだファイルのパス（`examples/basic.py` など）、`clone` |
| `confidence` | `high`：何ができるか・どう使うかがはっきり分かった／`medium`：だいたい分かったが一部が推測／`low`：材料が少なく、よく分からない |
| `confidence_note` | `medium` と `low` のときに理由を書きます（「README がほぼ画像だけ」など）。`high` なら `""` |

### tags の一覧

一覧の正本は `schemas/summary.schema.json` の `tags` です。サイトのカードの下に出て、どの分野のものかを一目で分かるようにします。

`AI エージェント`、`LLM`、`機械学習`、`音声・画像・動画`、`開発ツール`、`CLI`、`エディタ・IDE`、`データベース`、`データ処理`、`インフラ・運用`、`コンテナ・Kubernetes`、`ネットワーク`、`セキュリティ`、`監視・可観測性`、`Web`、`デスクトップアプリ`、`モバイル`、`セルフホスト`、`ライブラリ・SDK`、`言語・ランタイム`、`自動化・ワークフロー`、`ドキュメント・知識管理`、`学習資料`、`ゲーム`、`その他`

- 「何をするものか」で選ぶ。作られた言語や、README の宣伝の言葉（"AI-powered" など）では選ばない。AI を少し使っているだけのものに `LLM` を付けない
- 形（`CLI`、`デスクトップアプリ`、`セルフホスト`、`ライブラリ・SDK`）は、それが特徴のときだけ付ける
- どれにも当てはまらなければ `その他` だけにする

### 書き方の決まり

- **読者**は、日本のインフラ寄りのエンジニア1人です。英語を読むのがつらいので、このツールを使っています。
- 日本語で書きます。専門用語はカタカナにせず、英語のままでかまいません（`Kubernetes`、`reverse proxy`、`LLM`）。
- 文体は「だ・である」でも「です・ます」でもなく、**体言止めや短い常体**で簡潔に書きます（例：「HTTP サーバーに負荷をかける CLI。Go 製で1ファイル。」）。
- **盛らない。** README の宣伝文句（"blazingly fast"、"revolutionary"、"the best"）をそのまま訳しません。スター数が多いことも、よさの根拠として書きません。
- **分からないことは書かない。** 推測した部分は「〜と思われる」「〜に使えそう」と書きます。
- 「AI を活用した」「次世代の」のような、中身のない言い方をしません。何を入力して何が出てくるのかを書きます。
- README が他のサービスの宣伝の入口になっている（本体が有料 SaaS で、リポジトリは SDK だけ、など）なら、そう書きます。
- 学習用の教材、awesome リスト、講義資料のようなソフトウェアでないものは、そうと分かるように `what` に書きます（例：「OS の講義の教科書（LaTeX のソース）」）。`how_to_use` は「読み方」でかまいません。

### うまくいかないとき

- 材料が1つも集まっていない（`materials` が空）、リポジトリが消えている、などで要約を書けないときは、今日の `data/daily/YYYY-MM-DD.json` の `errors` に次の形で1件足して、次へ進みます。
  ```json
  {"repo": "owner/name", "reason": "何が起きたか（日本語で一文）"}
  ```
- 1件の失敗で全体を止めません。

## 3. 検査する

```bash
.venv/bin/python -m trending_digest validate
```

- `NG` が出たら、そのファイルの JSON を直して、もう一度 `validate` します。直すのは JSON だけです。
- `注意 …: 要約も errors の記録もない` が出たら、やり残しです。要約を書くか、`errors` に記録します。
- `OK` になるまで繰り返します。

## 4. コミットして push する

```bash
git add data/
git commit -m "YYYY-MM-DD の要約（N件）"
git push origin main
```

- コミットのメッセージは日本語です。要約できなかったものがあれば、本文に `owner/name: 理由` を1行ずつ書きます。
- push すると、GitHub Actions がサイトを作り直し、Discord に通知します。あなたの仕事はここまでです。

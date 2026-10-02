# 0027 OGP・sitemap・Atom フィードを出す、古い要約を書き直す、GitHub Pages をやめる

- 日付：2026-10-03
- 状態：決定

## 背景
ひとまず形になったので、本人と改善点を洗い出し、次をやることにした。
- Cloudflare Pages への移行（0008）が済んだので、GitHub Pages への二重の公開をやめる
- Discord や X に URL を貼ったときに、題と要約の入ったカードを出したい（OGP）
- 他のエンジニアにも届けたい（0006）。Discord に入っていない人には RSS リーダーで購読してもらうのが手軽
- 検索エンジンに見つけてもらえるようにする（sitemap など）
- 要約は一度書いたら使い回すので、数か月後にまた Trending に上がると、古い内容のまま出る

## 決定
- **GitHub Pages**：`daily.yml` から GitHub Pages への公開（configure-pages、upload-pages-artifact、deploy-pages）を外す。通知は Cloudflare Pages への公開が終わってから送る。リポジトリの Settings → Pages は本人が無効にする。`.nojekyll` も作らない
- **OGP と検索エンジン向けの情報**：全ページに `description`、`og:*`、`twitter:card`（`summary_large_image`）を出す。`site_base_url` があるときは、`canonical`、`og:url`、`og:image`（`og_image.png`、1200×630、題字を紙の色に置いたもの）と、フィードへの `<link rel="alternate">` も出す
  - description：一覧のページは「日付の GitHub Trending（期間）N件を日本語で要約。」と上位3件の `what`。詳しいページは `what` と `short`
  - 詳しいページの `og:type` は `article`、ほかは `website`
- **sitemap.xml と robots.txt**：全ページの URL と最終更新日（一覧はその日、詳しいページは要約した日）を sitemap に載せる。robots.txt は全部許可し、sitemap の場所を書く
- **Atom フィード（`/feed.xml`）**：要約1件を1記事にし、要約した日の新しい順に50件。題は「owner/name：what」、本文は `short`、リンクは詳しいページ、タグは category。時刻は持っていないので、要約した日の 7:00（日本時間）とする。RSS 2.0 ではなく Atom にしたのは、日付の書き方と ID の決まりがはっきりしていて、主なリーダーはどちらも読めるため
- 絶対 URL が要るものは `site_base_url` から作る。独自ドメインに移ったら `config.yaml` を直すだけでよい。`site_base_url` が空なら、sitemap・robots.txt・フィードは作らない
- **古い要約の書き直し**：`config.yaml` に `resummarize_after_days`（90）を足す。Trending に上がったものの要約が、その日から数えて90日以上前のものなら、queue に `refresh: true` として入れ、routine が今日の材料で書き直す（上書き）。書き直しは、要約のないものを全部入れたあとの、1日の上限の残りでだけ行う（新しいものを優先する）
  - routine の「すでに要約があるものは飛ばす」は、「`summarized_at` が今日の要約があるものは飛ばす」に変える（同じ日に routine が2回動いたときに二重に書かないため）

## 影響
- 詳しいページの URL は変わらないので、書き直しても、フィードでは同じ記事（同じ ID）の更新日が新しくなるだけ
- GitHub Pages の URL（https://koizumib.github.io/trending-digest/）は、Settings で無効にすると見られなくなる

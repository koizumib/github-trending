# 0028 名前を github-trending に決める

- 日付：2026-10-03
- 状態：決定

## 背景
名前は仮称の trending-digest のままだった（設計書の未決事項）。ひとまず形になったので、本人が名前を github-trending に決めた。

## 決定
- ソフトウェアの名前は **github-trending**
  - GitHub のリポジトリ：`koizumib/trending-digest` → `koizumib/github-trending`（本人が GitHub の Settings で変える。古い URL は GitHub が新しい URL へ自動で転送する）
  - Python のパッケージ：`trending_digest` → `github_trending`（`python -m github_trending …`）
  - User-Agent、Discord の知らせの頭（「⚠️ github-trending：…」）、文書、routine の名前と設定も合わせる
- 読者に見せるサイトの名前は、今までどおり **「github新聞」**
- Cloudflare Pages のプロジェクト `trending-digest` と URL `https://trending-digest.pages.dev/` は変えない。作り直すと URL が変わり、独自ドメインに移るときにもう一度変わるため。独自ドメインに移ったら `config.yaml` の `site_base_url` を直す
- 過去の設計判断（0001〜0027）とコミットのメッセージの中の旧名は、そのときの記録なので直さない

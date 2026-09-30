# 0008 サイトの公開先を Cloudflare Pages に移す

- 日付：2026-09-30
- 状態：決定（移行中）

## 背景
本人から「GitHub Pages を Cloudflare Pages に移したい」とのこと。本人はふだん Cloudflare を使っていて、独自ドメインや DNS も Cloudflare で扱う。

## 決定
- HTML は今までどおり GitHub Actions（`daily.yml`）で作り、`cloudflare/wrangler-action` の `pages deploy` で Cloudflare Pages に送る（Direct Upload）。Cloudflare Pages を GitHub のリポジトリに直接つなぐ方法（Git 連携）は使わない
  - 理由：「作る → 公開する → Discord に通知する」の順番を1つの workflow の中に保てる。Git 連携だと、公開と通知が別々に動き、公開より先に通知が届くことがある。毎朝の data/ の記録のコミットでビルドが走ることもない
- Cloudflare の API トークン（Cloudflare Pages の編集権限だけ）とアカウント ID は、GitHub の Secrets（`CLOUDFLARE_API_TOKEN`、`CLOUDFLARE_ACCOUNT_ID`）に置く
- Cloudflare Access での制限はかけない（誰でも見られる）
- 移行の順番：
  1. `daily.yml` で、GitHub Pages と Cloudflare Pages の両方に公開する
  2. Cloudflare の URL で開けることを確かめたら、`config.yaml` の `site_base_url`（通知に入るリンク）を Cloudflare の URL にする
  3. 数日ようすを見て、GitHub Pages への公開を外す

## あとで
- Cloudflare Pages ならリポジトリを非公開にしても公開できる。公開サービスにするかどうか（0006）と合わせて考える
- 独自ドメインは、名前を決めるときに Cloudflare でつなぐ

# 運用の手引き

毎朝どう動いているか、Discord に知らせが来たら何を見ればよいか、手で動かし直すにはどうするかを書く。仕組みの全体は `docs/design.md` の §3。

## 毎朝の流れ（日本時間）

| 時刻 | 何が | どこで見るか |
|---|---|---|
| 6:00 ごろ | Actions「取得と材料集め」：Trending の取得、data/ の記録、材料を work ブランチへ | GitHub の Actions タブ |
| 7:08 ごろ | routine「trending-digest 毎朝の要約」：要約を書いて main に push | https://claude.ai/code/routines/trig_01VBSyXRh8g9UMrCLPSrneVQ |
| push の数分後 | Actions「サイトを作って公開する」：サイトの更新（Cloudflare Pages）、Discord への通知 | Actions タブ、Discord、https://trending-digest.pages.dev/ |
| 9:00 | Actions「見張り」：取得の失敗を知らせる、未送信なら送る | Actions タブ、Discord |

- Actions の定期実行（cron）は、GitHub が混んでいると10〜30分ほど遅れることがある
- routine の要約は、15件でおおむね10〜40分
- 通知がいつもより遅くても、9時の見張りまでに届けば正常の範囲

## Discord に来る知らせと、見るところ

| 知らせ | 意味 | 見るところ |
|---|---|---|
| ⚠️ 取得と材料集め（prepare）が失敗しました | Trending のページを読み取れなかった（GitHub のページの構造が変わった、など）か、材料集めの途中で止まった | Actions タブの「取得と材料集め」の赤い実行 → 失敗した段階のログ |
| ⚠️ YYYY-MM-DD の Trending をまだ取得できていません | 9時になっても今日の data/daily/ がない。6時の Actions が動かなかったか失敗した | 同上。実行自体がなければ、GitHub 側の遅れか、定期実行が止まっている |
| ⚠️ 9時までに要約が N 件そろわなかったので、そのまま送ります | routine が終わらなかった、失敗した、または動かなかった | routine の管理画面 → 今日の実行 → セッションの記録 |
| ⚠️ 要約に失敗したものが多い | routine が `errors` に多く記録した | `data/daily/YYYY-MM-DD.json` の `errors` |
| 何も来ない | 通知の Actions が失敗した、または Webhook の URL が無効 | Actions タブの「サイトを作って公開する」と「見張り」 |
| サイトが更新されない | 「サイトを作って公開する」の「Cloudflare Pages に公開する」の段階が失敗した（API トークンの期限切れ・権限不足など） | その段階のログ。Cloudflare のダッシュボードの Pages → trending-digest の Deployments |

Actions が失敗すると、GitHub からメールも届く。

## 手で動かし直す

### Actions を手で動かす
1. https://github.com/koizumib/trending-digest/actions を開く
2. 左の一覧から workflow を選ぶ（「取得と材料集め」「サイトを作って公開する」「見張り」）
3. 右の「Run workflow」→ ブランチは `main` のまま →「Run workflow」

- 「取得と材料集め」は、今日の分がもう data/ にあれば Trending を取り直さず、その記録を使う
- 「見張り」を手で動かすと、今日の分をまだ送っていなければ送る

### routine を手で動かす
- routine の管理画面（上の URL）にある「今すぐ実行する」ボタンを押す。または Claude Code で `/schedule` を開き、「trending-digest の routine を今すぐ動かして」と頼む
- 6時の取得が終わる前に動かすと、30分待っても材料が来なければ何もせずに終わる

### Discord に送り直す
今日の分はもう送った、と記録されている日に送り直すには、手元で:

```bash
.venv/bin/python -m trending_digest notify --dry-run    # 送る内容を確かめる
.venv/bin/python -m trending_digest notify --force      # 送る（.env に DISCORD_WEBHOOK_URL が要る）
```

## 止める・再開する

- **routine**：管理画面でオフにする。Claude Code から `/schedule` で「一時停止して」と頼んでもよい。止めている間は要約が書かれず、9時の見張りが要約なしで通知を送る
- **Actions の定期実行**：Actions タブで workflow を選び、右上の「…」→「Disable workflow」
- GitHub は、60日間リポジトリに変更がないと定期実行を自動で止める。このツールは毎日 data/ をコミットするので、動いている限り止まらない

## よくあるつまずき

| 起きたこと | 原因 | 対処 |
|---|---|---|
| routine の材料集めで GitHub API が全部 403 | クラウドの実行環境では、割り当てたリポジトリ以外への GitHub API 呼び出しが止められる | 材料集めは Actions でやる（今の形。0007） |
| routine で `requires a different Python: 3.11` | クラウドの `python3` が 3.11 | `python3.12` で `.venv` を作る（手順書に記載済み） |
| routine の `git push origin main` が non-fast-forward | clone 直後が detached HEAD | `git push origin HEAD:main`（手順書に記載済み） |
| push したのに Actions が1つも動かない | コミットのメッセージのどこかに `[skip ci]` と書いた | 自動で記録するコミット以外では、メッセージに `[skip ci]` と書かない |
| routine のセッションが一覧で「active」のまま残る | routine のセッションは終わっても閉じられない | 終わったものはアーカイブしてよい。実行中かどうかは記録の最後で分かる |

## ロゴを差し替える

原本（大きい PNG、透明の背景）は `assets/logo/logo_light.png`（黒）と `logo_dark.png`（白）。サイトには、縮めて軽くしたものを `src/trending_digest/static/` に置く。原本を差し替えたら、次で作り直す（Pillow は作業用の仮想環境にだけ入れる。このツールの依存には足さない）。

```bash
python3.12 -m venv /tmp/imgvenv && /tmp/imgvenv/bin/pip install -q pillow
/tmp/imgvenv/bin/python - <<'EOF'
from PIL import Image
for name in ("light", "dark"):
    im = Image.open(f"assets/logo/logo_{name}.png").convert("RGBA")
    im = im.crop(im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox())  # 透明の余白を切る
    im = im.resize((1040, round(im.height * 1040 / im.width)), Image.LANCZOS)          # 横 1040px
    im.quantize(colors=16, method=Image.Quantize.FASTOCTREE).save(
        f"src/trending_digest/static/logo_{name}.png", optimize=True)                  # 16色で軽く
EOF
```

縦横の比が変わったら、`templates/base.html` の `<img>` の `width`・`height` も合わせる。

## 紙の質感の画像を差し替える

原本は `assets/texture/paper_texture.webp`。サイトには、凹凸の明暗だけを取り出して軽くしたものを置く（0018）。

```bash
/tmp/imgvenv/bin/python - <<'EOF'
from PIL import Image, ImageFilter, ImageChops, ImageEnhance
im = Image.open("assets/texture/paper_texture.webp").convert("L")
hp = ImageChops.subtract(im, im.filter(ImageFilter.GaussianBlur(24)), offset=128)  # 大きなむらを引く
hp = ImageEnhance.Contrast(hp).enhance(1.8)                                           # 凹凸を少し強く
hp = hp.resize((1000, round(hp.height * 1000 / hp.width)), Image.LANCZOS)
hp.save("src/trending_digest/static/paper_texture.webp", "WEBP", quality=40, method=6)
EOF
```

濃さは `style.css` の `--texture-opacity`（ライト）で変える。

## 外で設定したもの

`docs/design.md` の §8 にまとめている（GitHub の Secrets と Pages、routine の設定と実行環境）。

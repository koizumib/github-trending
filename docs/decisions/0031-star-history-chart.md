# 0031 詳しいページの「基本データ」に、star-history.com のスターの推移の画像を入れる

- 日付：2026-10-03
- 状態：決定

## 背景
本人から、詳しいページの基本データに star-history.com のグラフを入れたい、と。今のスター数だけでは、急に伸びたのか、前から人気なのかが分からない。

## 決定
- 基本データの枠の末尾に「スターの推移」として、`https://api.star-history.com/chart?repos=owner/name&type=date` の画像（SVG）を置く。押すと star-history.com のそのリポジトリのページを開く
- 画像は読む人のブラウザが star-history.com から取りに行く。こちらのスクリプト（Actions・prepare）は取りに行かない（取得の回数も、判断も増えない）
- star-history.com が勧める `<picture>` と `prefers-color-scheme` の形は使わない。それだと端末の設定で明暗が決まり、サイトのテーマ切り替えに追従しないため。ロゴと同じく、ライト用と `theme=dark` の2枚を置いて CSS で出し分ける。`loading="lazy"` なので、隠れている方は読み込まれない
- リポジトリ名は小文字にして渡す（大文字のままだと、star-history.com が小文字の URL へ転送する分、1回余計に往復する）
- 画像を読み込めなかったら（star-history.com が落ちている、制限に当たったなど）、その欄ごと隠す
- 幅は枠に合わせ、PC では 640px まで。枠の中で中央に置く

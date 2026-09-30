# 設計判断の記録

設計を変えるときは、ここにファイルを1つ足してから実装する（`CLAUDE.md`）。1判断1ファイル。番号は増やすだけで、振り直さない。あとの判断で上書きされたものも消さずに残す。

| 番号 | 判断 | 日付 | 状態 |
|---|---|---|---|
| [0001](0001-classify-gap-within-window.md) | 10日以内に間が空いて戻ってきたものは continuing にする | 2026-09-30 | 有効 |
| [0002](0002-summarize-with-claude-code-routine.md) | 要約は Claude API ではなく Claude Code の routine で書く | 2026-09-30 | 有効（routine で prepare を動かす部分は 0007 で変更） |
| [0003](0003-site-glass-and-theme-toggle.md) | サイトの見た目：PC では2列、グラスモーフィズム、テーマの切り替え | 2026-09-30 | テーマの切り替えだけ有効。見た目は 0009 で置き換え |
| [0004](0004-summary-tags.md) | 要約に分野のタグ（tags）を足す | 2026-09-30 | 有効 |
| [0005](0005-weekly-monthly.md) | ウィークリーとマンスリーの Trending も取る | 2026-09-30 | 有効 |
| [0006](0006-public-via-discord.md) | 他のエンジニアにも公開し、届け方は Discord を本命にする | 2026-09-30 | 方向は決定。まず本人だけで試す |
| [0007](0007-prepare-on-actions.md) | 取得と材料集め（prepare）は GitHub Actions で動かす | 2026-09-30 | 有効 |
| [0008](0008-cloudflare-pages.md) | サイトの公開先を Cloudflare Pages に移す（Actions で作って Direct Upload） | 2026-09-30 | 移行中 |
| [0009](0009-simple-design.md) | サイトの見た目をシンプルにする（グラスモーフィズムをやめる） | 2026-09-30 | 有効 |

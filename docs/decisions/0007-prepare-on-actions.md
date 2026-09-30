# 0007 取得と材料集め（prepare）は GitHub Actions で動かす

- 日付：2026-09-30
- 状態：決定

## 背景
routine（Claude Code のクラウドの実行環境）で `prepare` を動かしたところ、GitHub API の `/repos/{owner}/{repo}` がすべて HTTP 403 になった。クラウドの実行環境では GitHub への通信が専用の中継（プロキシ）を通り、routine に割り当てたリポジトリ（trending-digest）以外への API 呼び出しは届かない（「GitHub access to this repository is not enabled for this session」）。ネットワークを Full にしても変わらない。

## 決定
役割を、次のように分け直す。

```
6:00 ごろ  GitHub Actions（prepare.yml）
           prepare：Trending（3ページ）の取得、分類、材料集め
           → data/ を main に push（[skip ci] を付け、この push では公開・通知をしない）
           → 材料（.work/ の中身）を work ブランチに上書きで push
7:00 ごろ  Claude Code の routine
           work ブランチの材料を .work/ に展開 → 要約を書く → validate → main に push
           → push をきっかけに daily.yml が公開と Discord への通知をする
9:00      GitHub Actions（watchdog.yml）
           今日の data/daily/ がなければ「取得に失敗した」と知らせる
           今日の分がまだ送られていなければ、要約のあるなしにかかわらず送る（送ったと記録する）
```

- Actions では `GITHUB_TOKEN` で GitHub API を呼ぶ（1時間に1,000回まで）
- 材料は `main` に入れない（毎日数百 KB 増えるため）。`work` ブランチは毎回1コミットだけの状態で上書きする
- `prepare` が失敗したら（Trending を読み取れない）、その workflow から Discord に知らせる
- routine は `prepare` を動かさない。`work` ブランチの queue の日付が今日でなければ、数分おきに見直し、30分待っても来なければ何もせずに報告して終わる
- routine が要約するものが0件の日や、routine が失敗した日も、9時の見張りが通知を送るので、通知が途切れない

## 考えたほかの案
- routine の中で、API を使わずに材料を集める（raw.githubusercontent.com、Web ページの読み取り、clone）。説明文・スター数・ライセンスを取るには Web ページを読み取ることになり、「リポジトリの情報は API で取る」という原則から外れるのでやめた
- Actions の prepare の終わりに routine を呼び出す（webhook）。時刻のずれに強いが、仕組みが増える。cron の間隔（1時間）と routine の待ち時間で足りなければ考える

# 0002 要約は Claude API ではなく Claude Code の routine で書く

- 日付：2026-09-30
- 状態：決定（設計書 v0.2）

## 背景
最初の設計（v0.1）では、GitHub Actions から Claude API を呼んで要約する予定だった。本人は Claude API を契約していない。

## 決定
- 毎朝、Claude Code の routine（クラウドでの定期実行）が `prepare` → 要約 → `validate` → push をする
- 要約の手順は `docs/routine.md` に書く。routine のプロンプトは「`docs/routine.md` に従って」だけにする
- GitHub Actions は push をきっかけに build・deploy・notify だけをする
- 依存から `anthropic` を外し、要約の形の検査のために `jsonschema` を足す
- `config.yaml` から `model` を外す

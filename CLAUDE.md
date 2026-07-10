# CLAUDE.md

## 応答ルール

- 常に日本語で応答すること。

## プロジェクト概要

このリポジトリは、LLM（大規模言語モデル）に関する学習とポートフォリオ制作を目的としたプロジェクトです。

最終的な成果物として **TechDoc QA Bot** を開発します。これは開発者向けの技術ドキュメント特化型 AI チャットボットで、アップロードされたドキュメント（PDF・Markdown など）に対して自然言語で質問すると、RAG（検索拡張生成）技術を用いて根拠となる参照元とともに的確な回答を返すツールです。

### 主な機能（将来的な目標）

- 複数ドキュメントの一括学習・Q&A
- 回答の参照元（根拠）の提示
- 会話履歴の保持
- ストリーミング応答

### 技術スタック（想定）

- バックエンド: FastAPI
- AI/LLM: LangChain, OpenAI, Claude
- ベクトルDB: ChromaDB（開発初期）, PostgreSQL（本番想定）
- インフラ: Docker
- クラウド（予定）: Amazon ECS, Amazon S3

### ディレクトリ構成

- `01_basics/`: Git・コマンドライン・Python・SQLなどの基礎学習
- `02_speciality/`: Docker・FastAPI・LangChainなどの専門技術の学習
- `03_portfolio/`: ポートフォリオ成果物（TechDoc QA Bot など）

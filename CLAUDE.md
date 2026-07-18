# CLAUDE.md

## 応答ルール

- 常に日本語で応答すること。

## プロジェクト概要

このリポジトリは、LLM（大規模言語モデル）に関する学習記録と、複数のポートフォリオ作品を含むプロジェクトです。`03_portfolio/` 配下に、独立した作品を1つずつ追加していく方針です。

### ポートフォリオ作品

#### TechDoc QA Bot（完成済み）

開発者向けの技術ドキュメント特化型 AI チャットボット。アップロードしたPDFに自然言語で質問すると、RAG（検索拡張生成）技術を用いて根拠となる参照元とともに回答します。

- 実装: Python + LangChain + ChromaDB + Claude Haiku 4.5（回答生成）+ OpenAI Embeddings（`text-embedding-3-small`）
- RAG精度評価の仕組み（キーワードベースの自動採点）と、埋め込みモデル・chunk_size・top_kの選定根拠のドキュメント化が完了
- pytestによる回帰テストとGitHub Actions CIが整備済み
- 詳細: `03_portfolio/techdoc-qa-bot/README.md`、`03_portfolio/techdoc-qa-bot/docs/evaluation.md`

#### skill-match-analyzer（要件定義中）

求人票・案件票のテキストと自分のスキルプロファイルを突き合わせ、マッチ度・根拠・ギャップなどを構造化出力するツール。詳細は `03_portfolio/skill-match-analyzer/docs/requirements.md` を参照。

### ディレクトリ構成

- `01_basics/`: Git・コマンドライン・Python・SQLなどの基礎学習
- `02_speciality/`: Docker・FastAPI・LangChainなどの専門技術の学習
- `03_portfolio/`: ポートフォリオ成果物（各サブディレクトリが独立したプロジェクト）

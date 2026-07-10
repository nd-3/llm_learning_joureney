# 要件定義書

## プロダクト名

TechDoc QA Bot

## 目的

技術ドキュメント（PDF）を読み込ませ、質問すると根拠付きで回答する RAG（検索拡張生成）システムを構築する。

## MVP スコープ

- PDF は 1 つのみ対応
- コンソール入力（CLI）でのやり取り
- 会話履歴なし（毎回単発の質問応答）
- ストリーミング応答なし

## 技術スタック

- 言語: Python
- フレームワーク: LangChain
- Embedding: OpenAI Embedding
- LLM: Claude Haiku（切り替え可能な設計とする）
- ベクトルDB: ChromaDB
- PDF読み込み: pypdf

## 成功の定義

1 つの PDF について質問すると、その内容に基づいた回答が返ってくること。

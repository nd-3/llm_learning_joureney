# TechDoc QA Bot 🤖（LLM 学習　ポートフォリオ用）

[![Status: In Progress](https://img.shields.io/badge/Status-In_Progress-yellow)](https://github.com/あなたのユーザー名/TechDoc-QA-Bot)
[![Python Version](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Framework: FastAPI](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**TechDoc QA Bot**は、開発者向けの技術ドキュメント特化型 AI チャットボットです。自然言語で質問するだけで、アップロードされた複数のドキュメントから的確な回答と参照元を見つけ出し、使用者の技術調査を加速させます。

---

![UI Screenshot Placeholder](https://via.placeholder.com/800x400.png?text=アプリケーションのスクリーンショットまたはデモGIF)
（ここにアプリケーションのスクリーンショットや、動いている様子の GIF アニメーション等を挿入予定）

## 💡 プロジェクトの背景 (Motivation)

新しい技術を学ぶ際、膨大な公式ドキュメントや複数の技術ブログを読む中で、「この機能について、もっと簡潔に知りたい」「複数のページにまたがる情報を一箇所で確認したい」と感じることが多々ある。

この体験から、自身の課題を解決するツールとして、RAG(検索拡張生成)技術を用いた本プロジェクトの開発を開始しました。このツールは、開発者がより本質的な学びに集中できる環境を提供することを目指しています。

## ✨ 主な機能 (Features)

- **📚 複数ドキュメントの一括学習:** 複数の PDF や Markdown ファイルをアップロードし、それら全体を知識源とした Q&A が可能です。
- **🔗 参照元の提示:** AI が生成した回答の根拠となったドキュメントの箇所を明示し、情報の信頼性を担保します。
- **💬 会話履歴の保持:** セッションごとに会話の文脈を記憶し、より深い対話を実現します。
- **💨 ストリーミング応答 (実装予定):** ChatGPT のように、回答をリアルタイムで順次表示する機能を実装し、ユーザーの体感待ち時間を改善します。

## 🛠️ 技術スタック & アーキテクチャ

このプロジェクトは、パフォーマンスと拡張性を考慮し、以下の技術スタックで構築予定です。

| カテゴリ            | 技術                                                                                                                                                                                     |
| :------------------ | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **バックエンド**    | <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" />                                                                                                   |
| **AI/LLM**          | <img src="https://img.shields.io/badge/LangChain-FFFFFF?logo=langchain&logoColor=black" /> <img src="https://img.shields.io/badge/OpenAI-412991?logo=openai&logoColor=white" />          |
| **ベクトル DB**     | **ChromaDB** (開発初期), **PostgreSQL** (本番想定)                                                                                                                                       |
| **インフラ**        | <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" />                                                                                                     |
| **クラウド (予定)** | <img src="https://img.shields.io/badge/Amazon_ECS-FF9900?logo=amazon-aws&logoColor=white" /> <img src="https://img.shields.io/badge/Amazon_S3-569A31?logo=amazon-aws&logoColor=white" /> |

### アーキテクチャ図

```mermaid
graph TD
    subgraph User Interaction
        A[ユーザー] -->|質問(HTTP Request)| B(FastAPI Backend);
    end

    subgraph RAG Pipeline
        B -->|テキストチャンク| C(Embedding Model);
        C -->|ベクトル化| D[Vector Store (ChromaDB)];
        B -->|検索クエリ| D;
        D -->|関連コンテキスト| B;
        B -->|コンテキスト + 質問プロンプト| E(LLM API);
        E -->|生成された回答| B;
    end

    subgraph Response
        B -->|ストリーミング応答| A;
    end
```

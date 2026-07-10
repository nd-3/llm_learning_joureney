"""TechDoc QA Bot - RAG最小実装(MVP)

PDFを1つ読み込み、コンソールで質問を受け付けて
根拠付きで回答するシンプルなRAGシステム。
"""

import argparse
import os
import sys

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ChromaDBの永続化先ディレクトリ(このファイルから見て ../data/chroma_db)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHROMA_DB_DIR = os.path.join(BASE_DIR, "data", "chroma_db")

# チャンク分割の設定
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# 検索時に取得する関連チャンク数
RETRIEVE_TOP_K = 4

# 使用するLLMモデル(切り替え可能: 例 "claude-opus-4-8" など)
CLAUDE_MODEL = "claude-haiku-4-5"


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する(PDFファイルのパスを受け取る)。"""
    parser = argparse.ArgumentParser(description="PDFに対して質問応答を行うRAGボット")
    parser.add_argument("pdf_path", help="読み込むPDFファイルのパス")
    return parser.parse_args()


def load_api_keys() -> None:
    """.envからAPIキーを読み込み、未設定の場合はエラー終了する。"""
    load_dotenv()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("エラー: ANTHROPIC_API_KEYが.envに設定されていません。")
    if not os.environ.get("OPENAI_API_KEY"):
        sys.exit("エラー: OPENAI_API_KEYが.envに設定されていません。")


def build_vector_store(pdf_path: str) -> Chroma:
    """PDFを読み込み、チャンク分割してベクトル化し、ChromaDBに永続化する。

    既にDBが永続化済みの場合は、再読み込み・再ベクトル化を行わず
    既存のDBを再利用する(APIコストと処理時間の節約のため)。
    """
    embeddings = OpenAIEmbeddings()

    if os.path.exists(CHROMA_DB_DIR):
        print(f"既存のベクトルDBを再利用します: {CHROMA_DB_DIR}")
        return Chroma(
            persist_directory=CHROMA_DB_DIR,
            embedding_function=embeddings,
        )

    print(f"PDFを読み込み中: {pdf_path}")
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    print("テキストをチャンク分割中...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    chunks = splitter.split_documents(documents)
    print(f"{len(chunks)}個のチャンクに分割しました。")

    print("ベクトル化してChromaDBに保存中...")
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DB_DIR,
    )
    print(f"ベクトルDBを永続化しました: {CHROMA_DB_DIR}")

    return vector_store


def build_prompt(question: str, context_chunks: list[str]) -> list:
    """検索で得たコンテキストと質問から、LLMに渡すメッセージを組み立てる。"""
    context_text = "\n\n---\n\n".join(context_chunks)

    system_prompt = (
        "あなたは与えられた資料の内容に基づいて質問に答えるアシスタントです。"
        "以下の「参考資料」の内容のみを根拠として回答してください。"
        "参考資料に答えが見つからない場合は、推測せずに"
        "「資料からは判断できません」と answer してください。"
    )

    human_prompt = f"""# 参考資料
{context_text}

# 質問
{question}
"""

    return [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]


def answer_question(vector_store: Chroma, llm: ChatAnthropic, question: str) -> str:
    """質問に関連するチャンクを検索し、LLMに回答を生成させる。"""
    relevant_docs = vector_store.similarity_search(question, k=RETRIEVE_TOP_K)
    context_chunks = [doc.page_content for doc in relevant_docs]

    messages = build_prompt(question, context_chunks)
    response = llm.invoke(messages)

    return response.content


def run_qa_loop(vector_store: Chroma) -> None:
    """コンソールで質問を受け付け続けるループ。"""
    llm = ChatAnthropic(model=CLAUDE_MODEL)

    print("\n質問を入力してください(終了するには 'exit' または 'quit' と入力)。")
    while True:
        question = input("\n質問> ").strip()
        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            print("終了します。")
            break

        answer = answer_question(vector_store, llm, question)
        print(f"\n回答: {answer}")


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.pdf_path):
        sys.exit(f"エラー: 指定されたPDFファイルが見つかりません: {args.pdf_path}")

    load_api_keys()
    vector_store = build_vector_store(args.pdf_path)
    run_qa_loop(vector_store)


if __name__ == "__main__":
    main()

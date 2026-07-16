"""RAG精度評価スクリプト

evals/qa_dataset.json の全問について、既存のRAGパイプライン(src/main.py)を
実際に動かし、検索結果と生成回答をキーワードベースで採点する。

評価用のベクトルDBは data/chroma_db (本番用) とは別に、設定(埋め込みモデル・
チャンクサイズ)ごとに evals/db/{model}_{chunksize}/ へ構築する。異なる埋め込み
モデルのベクトルを同じDBに混在させないため。
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

# src/main.py の関数をそのまま再利用するため、srcディレクトリをインポートパスに追加する。
EVALS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(EVALS_DIR)
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.insert(0, SRC_DIR)

import main as rag  # noqa: E402 (sys.path設定後にimportする必要がある)
from langchain_anthropic import ChatAnthropic  # noqa: E402

DEFAULT_DATASET_PATH = os.path.join(EVALS_DIR, "qa_dataset.json")
DEFAULT_PDF_PATH = os.path.join(PROJECT_ROOT, "data", "sample.pdf")
DB_ROOT_DIR = os.path.join(EVALS_DIR, "db")
RESULTS_DIR = os.path.join(EVALS_DIR, "results")

# not_in_doc問題の「資料に記載がない」旨の判定に使うフレーズ。
# main.pyのシステムプロンプト(build_prompt関数)は、資料に答えがない場合
# 「資料からは判断できません」と回答するよう明示的に指示しているため、
# それを主軸に、表現ゆれを吸収するための類似フレーズも許容する。
# (回答にこれらのいずれかが部分文字列として含まれていればOKと判定する)
NOT_IN_DOC_PHRASES = (
    "資料からは判断できません",
    "資料に記載がありません",
    "資料には記載がありません",
    "記載がありません",
    "記載がない",
    "わかりません",
)


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する。"""
    parser = argparse.ArgumentParser(description="RAGパイプラインの精度評価を実行する")
    parser.add_argument(
        "--embedding-model",
        default=rag.EMBEDDING_MODEL,
        help=f"OpenAI Embeddingsのモデル名(デフォルト: {rag.EMBEDDING_MODEL})",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=rag.CHUNK_SIZE,
        help=f"テキスト分割時のチャンクサイズ(デフォルト: {rag.CHUNK_SIZE})",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=rag.RETRIEVE_TOP_K,
        help=f"検索時に取得する上位チャンク数(デフォルト: {rag.RETRIEVE_TOP_K})",
    )
    parser.add_argument(
        "--pdf",
        dest="pdf_path",
        default=DEFAULT_PDF_PATH,
        help=f"評価対象のPDFファイルパス(デフォルト: {DEFAULT_PDF_PATH})",
    )
    parser.add_argument(
        "--dataset",
        default=DEFAULT_DATASET_PATH,
        help=f"QAデータセットのJSONパス(デフォルト: {DEFAULT_DATASET_PATH})",
    )
    return parser.parse_args()


def sanitize_for_filename(value: str) -> str:
    """ディレクトリ名・ファイル名として安全な文字列に変換する(英数字・.・-・_以外は_に置換)。"""
    return re.sub(r"[^\w.-]", "_", value)


def load_dataset(path: str) -> list[dict]:
    """QAデータセットのJSONを読み込む。"""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


# qa_dataset*.json の expected_keywords は、単純な部分文字列一致による
# 活用形・語順のズレを避けるため、以下のルールで記述する:
#   1. 名詞または語幹で書く(例:「読みやすい」ではなく「読みやす」と書き、
#      「読みやすい」「読みやすく」「読みやすかった」などの活用をまとめて拾う)
#   2. 複合フレーズは単語単位に分割して複数キーワードにする
#      (例:「シンプルな文法」ではなく「シンプル」と「文法」の2キーワードにする)
# この関数自体は単純な部分文字列一致(contains)のみを行い、形態素解析などは
# 行わない。キーワード側を上記ルールで書くことで、シンプルな実装のまま
# 活用形・語順による誤判定を減らす設計としている。
#
# また、比較前に半角・全角スペースや改行などの空白文字をすべて除去して
# 正規化する。これはpypdfのPDFテキスト抽出が、両端揃え(ジャスティファイ)
# されたレイアウトの都合で、半角文字(数字・アルファベット)と日本語文字の
# 間に不要な半角スペースを挿入してしまう癖への対策である
# (例:「1989年」が本文からは「1989 年」として抽出される)。
# この空白は意味を持たないレイアウト上のノイズであり、キーワード側にも
# チャンク本文側にも一律に発生しうるため、双方から除去してから比較する。
_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_for_match(text: str) -> str:
    """空白文字(半角・全角・改行)をすべて除去し、大文字小文字を無視した形に正規化する。"""
    return _WHITESPACE_RE.sub("", text).lower()


def contains_all_keywords(text: str, keywords: list[str]) -> bool:
    """textに、keywordsの全てが(空白の有無・大文字小文字を無視して)部分文字列として含まれるか判定する。"""
    normalized = _normalize_for_match(text)
    return all(_normalize_for_match(keyword) in normalized for keyword in keywords)


def is_not_in_doc_answer(text: str) -> bool:
    """回答が「資料に記載がない」旨を述べているかを、NOT_IN_DOC_PHRASESのいずれかを
    含むかどうかで判定する。"""
    return any(phrase in text for phrase in NOT_IN_DOC_PHRASES)


def evaluate_question(vector_store, llm: ChatAnthropic, item: dict, top_k: int) -> dict:
    """1問について検索・回答生成・採点を行う。"""
    question = item["question"]
    q_type = item["type"]
    expected_keywords = item["expected_keywords"]

    retrieved_chunks = rag.retrieve_relevant_chunks(vector_store, question, k=top_k)
    answer = rag.generate_answer(llm, question, retrieved_chunks)

    # 検索評価: not_in_docは正解チャンクがそもそも存在しないため対象外(Noneのまま)。
    # single/multiは、取得した上位チャンクを結合したテキストに expected_keywords が
    # 「すべて」含まれていれば検索成功とみなす(回答評価と基準を揃えるための設計判断)。
    retrieval_hit = None
    if q_type != "not_in_doc":
        combined_chunks_text = "\n".join(retrieved_chunks)
        retrieval_hit = contains_all_keywords(combined_chunks_text, expected_keywords)

    # 回答評価: single/multiは回答にexpected_keywordsが全て含まれればOK。
    # not_in_docは「記載がない」旨の定型的な回答をしていればOK。
    if q_type == "not_in_doc":
        answer_correct = is_not_in_doc_answer(answer)
    else:
        answer_correct = contains_all_keywords(answer, expected_keywords)

    return {
        "id": item["id"],
        "type": q_type,
        "question": question,
        "expected_keywords": expected_keywords,
        "reference_answer": item["reference_answer"],
        "retrieved_chunks": retrieved_chunks,
        "retrieval_hit": retrieval_hit,
        "answer": answer,
        "answer_correct": answer_correct,
    }


def _rate(results: list[dict]) -> dict:
    """resultsのリストから正解数・問題数・正解率を計算する。"""
    correct = sum(1 for r in results if r["answer_correct"])
    total = len(results)
    return {
        "total": total,
        "correct": correct,
        "accuracy": correct / total if total else 0.0,
    }


def summarize(results: list[dict]) -> dict:
    """種別ごと + 全体の正解率と、検索ヒット率を集計する。"""
    summary = {"overall": _rate(results)}
    for q_type in ("single", "multi", "not_in_doc"):
        summary[q_type] = _rate([r for r in results if r["type"] == q_type])

    retrieval_targets = [r for r in results if r["retrieval_hit"] is not None]
    retrieval_hits = sum(1 for r in retrieval_targets if r["retrieval_hit"])
    summary["retrieval"] = {
        "total": len(retrieval_targets),
        "hit": retrieval_hits,
        "hit_rate": retrieval_hits / len(retrieval_targets) if retrieval_targets else 0.0,
    }
    return summary


def print_summary(summary: dict) -> None:
    """種別ごと+全体の正解率と、検索ヒット率のサマリ表をコンソールに表示する。"""
    label_map = {"single": "single", "multi": "multi", "not_in_doc": "not_in_doc", "overall": "全体"}

    print("\n" + "=" * 60)
    print("評価サマリ")
    print("=" * 60)
    print(f"{'種別':<12}{'正解数':>8}{'問題数':>8}{'正解率':>10}")
    print("-" * 60)
    for key in ("single", "multi", "not_in_doc", "overall"):
        s = summary[key]
        print(f"{label_map[key]:<12}{s['correct']:>8}{s['total']:>8}{s['accuracy'] * 100:>9.1f}%")

    r = summary["retrieval"]
    print("-" * 60)
    print(f"検索ヒット率(single/multiのみ対象): {r['hit']}/{r['total']} ({r['hit_rate'] * 100:.1f}%)")
    print("=" * 60)


def print_incorrect(results: list[dict]) -> None:
    """不正解だった問題を一覧表示する。"""
    incorrect = [r for r in results if not r["answer_correct"]]
    if not incorrect:
        print("\n不正解の問題はありませんでした。")
        return

    print(f"\n不正解の問題({len(incorrect)}件):")
    print("-" * 60)
    for r in incorrect:
        print(f"ID {r['id']} [{r['type']}] {r['question']}")
        print(f"  実際の回答: {r['answer']}")
        print()


def save_results(config: dict, summary: dict, results: list[dict], results_dir: str) -> str:
    """設定と全問の結果をJSONファイルに保存し、保存先パスを返す。"""
    os.makedirs(results_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_part = sanitize_for_filename(config["embedding_model"])
    filename = f"{timestamp}_{model_part}_{config['chunk_size']}.json"
    path = os.path.join(results_dir, filename)

    payload = {"config": config, "summary": summary, "results": results}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return path


def main() -> None:
    args = parse_args()
    rag.load_api_keys()

    dataset = load_dataset(args.dataset)

    # ディレクトリ名にPDFファイル名も含める。埋め込みモデル・チャンクサイズが
    # 同じでも評価対象のPDFが異なればベクトルの中身は別物になるため、
    # PDFを区別せずディレクトリを共有すると、異なる文書で評価したはずが
    # 古いPDFのベクトルDBを誤って再利用してしまう(実際に発生した不具合)。
    pdf_stem = os.path.splitext(os.path.basename(args.pdf_path))[0]
    db_dirname = f"{sanitize_for_filename(pdf_stem)}_{sanitize_for_filename(args.embedding_model)}_{args.chunk_size}"
    persist_dir = os.path.join(DB_ROOT_DIR, db_dirname)

    print(f"設定: embedding_model={args.embedding_model}, chunk_size={args.chunk_size}, top_k={args.top_k}")
    print(f"ベクトルDB: {persist_dir}")

    vector_store = rag.build_vector_store(
        args.pdf_path,
        persist_dir=persist_dir,
        embedding_model=args.embedding_model,
        chunk_size=args.chunk_size,
    )
    llm = ChatAnthropic(model=rag.CLAUDE_MODEL)

    print(f"\n{len(dataset)}問を評価中...")
    results = []
    for i, item in enumerate(dataset, start=1):
        print(f"  [{i}/{len(dataset)}] ID {item['id']}: {item['question']}")
        results.append(evaluate_question(vector_store, llm, item, top_k=args.top_k))

    summary = summarize(results)
    print_summary(summary)
    print_incorrect(results)

    config = {
        "embedding_model": args.embedding_model,
        "chunk_size": args.chunk_size,
        "chunk_overlap": rag.CHUNK_OVERLAP,
        "top_k": args.top_k,
        "claude_model": rag.CLAUDE_MODEL,
        "pdf_path": args.pdf_path,
        "dataset_path": args.dataset,
    }
    saved_path = save_results(config, summary, results, RESULTS_DIR)
    print(f"\n結果を保存しました: {saved_path}")


if __name__ == "__main__":
    main()

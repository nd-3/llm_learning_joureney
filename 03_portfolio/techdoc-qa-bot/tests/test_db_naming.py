"""ベクトルDBの永続化ディレクトリ名の回帰テスト。

実際に踏んだバグ: ディレクトリ名が埋め込みモデル名(evals側はPDF名も)を
含んでいなかったため、設定を変えて実行/評価しても古いベクトルDBを
誤って再利用し、まったく見当違いの検索結果が返っていた
(経緯: docs/evaluation.md 測定系で発見・修正した問題 3.)。
"""

import main as rag
from run_eval import build_db_dirname


def test_main_chroma_db_dir_includes_embedding_model_name():
    assert rag.EMBEDDING_MODEL in rag.CHROMA_DB_DIR


def test_main_chroma_db_dir_differs_across_embedding_models():
    dir_a = rag.build_chroma_db_dir("/tmp/project", "text-embedding-ada-002")
    dir_b = rag.build_chroma_db_dir("/tmp/project", "text-embedding-3-small")
    assert dir_a != dir_b
    assert "text-embedding-ada-002" in dir_a
    assert "text-embedding-3-small" in dir_b


def test_eval_db_dirname_includes_pdf_name_and_embedding_model_and_chunk_size():
    dirname = build_db_dirname("data/sample.pdf", "text-embedding-3-small", 1000)
    assert "sample" in dirname
    assert "text-embedding-3-small" in dirname
    assert "1000" in dirname


def test_eval_db_dirname_differs_across_pdfs_for_same_model_and_chunk_size():
    # 同じモデル・チャンクサイズでも、PDFが異なればディレクトリ名も
    # 異なる必要がある(同一だと別文書のDBを取り違えてしまう)。
    dirname_sample = build_db_dirname("data/sample.pdf", "text-embedding-3-small", 1000)
    dirname_kyodai = build_db_dirname("data/kyodai_python_2023.pdf", "text-embedding-3-small", 1000)
    assert dirname_sample != dirname_kyodai


def test_eval_db_dirname_differs_across_embedding_models_for_same_pdf():
    dirname_ada = build_db_dirname("data/sample.pdf", "text-embedding-ada-002", 1000)
    dirname_small = build_db_dirname("data/sample.pdf", "text-embedding-3-small", 1000)
    assert dirname_ada != dirname_small

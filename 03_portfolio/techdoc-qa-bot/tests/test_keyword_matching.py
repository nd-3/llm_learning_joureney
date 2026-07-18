"""contains_all_keywords (evals/run_eval.py) の回帰テスト。

ここでのテストケースは、評価環境の構築中に実際に踏んだバグをそのまま
再現したものである(経緯: docs/evaluation.md 測定系で発見・修正した問題)。
"""

from run_eval import contains_all_keywords


def test_whitespace_normalization_matches_pypdf_space_artifact():
    # 実際に踏んだバグ: pypdfのテキスト抽出は半角文字と日本語の間に余計な
    # 空白を挿入する癖があり、本文の「1989年」が「1989 年」として抽出される。
    # 空白を正規化してから比較することで、この抽出結果でもヒットする。
    chunk_text = "Pythonの実装は1989 年にGuido van Rossumにより始まりました。"
    assert contains_all_keywords(chunk_text, ["1989年"])


def test_stem_keyword_matches_inflected_form():
    # 実際に踏んだバグ: キーワードを辞書形「読みやすい」のまま書くと、
    # 回答側の活用形「読みやすく」で部分一致が外れて誤って不正解判定になった。
    # 語幹形「読みやす」で書けば活用に関わらずヒットする。
    answer = "Pythonの文法はシンプルで読みやすく、初心者にも学びやすいです。"
    assert contains_all_keywords(answer, ["読みやす"])


def test_all_keywords_required_and_match():
    text = "Pythonはシンプルで読みやすい言語です。"
    assert contains_all_keywords(text, ["シンプル", "読みやすい"])


def test_all_keywords_required_partial_match_fails():
    # AND判定: 一部のキーワードしか含まれない場合は不一致となる。
    text = "Pythonはシンプルで読みやすい言語です。"
    assert not contains_all_keywords(text, ["シンプル", "存在しないキーワード"])


def test_case_insensitive_match():
    text = "NumPyは数値計算のライブラリです。"
    assert contains_all_keywords(text, ["numpy"])


def test_no_keywords_present_returns_false():
    text = "Pythonはインタプリタ言語です。"
    assert not contains_all_keywords(text, ["コンパイラ言語"])

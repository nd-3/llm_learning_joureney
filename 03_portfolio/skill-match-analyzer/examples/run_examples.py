"""examples/ 配下の架空求人票2件を、skill_profile.example.yaml に対して実行し、
成功の定義(docs/requirements.md)を検証するスクリプト。

- Claude APIを実際に呼び出すため、ANTHROPIC_API_KEYが必要(.env参照)。
- 出力がスキーマ(SkillMatchAnalysis)に完全準拠することは、Pydanticの
  client.messages.parse()が例外なく完了する時点で保証される。
- 加えて、matched_skillsの根拠(job_posting_quote)が実際に求人票本文に
  含まれているかを機械的に検証する(創作された引用でないことの確認)。
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from analyzer import load_api_key, load_profile  # noqa: E402
from analyzer import analyze  # noqa: E402

EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(EXAMPLES_DIR)
PROFILE_PATH = os.path.join(PROJECT_ROOT, "skill_profile.example.yaml")

JOB_FILES = {
    "LLMアプリケーションエンジニア(架空)": os.path.join(EXAMPLES_DIR, "job_sample_llm.txt"),
    "組込みソフトウェアエンジニア(架空)": os.path.join(EXAMPLES_DIR, "job_sample_embedded.txt"),
}


def verify_quotes_exist_in_job_text(result, job_text: str, label: str) -> list[str]:
    """matched_skillsのjob_posting_quoteが、すべて求人票本文に実在するか検証する。"""
    problems = []
    for matched in result.matched_skills:
        quote = matched.evidence.job_posting_quote
        if quote not in job_text:
            problems.append(f"[{label}] skill={matched.skill!r} の引用が本文に見つかりません: {quote!r}")
    return problems


def main() -> None:
    load_api_key()
    profile = load_profile(PROFILE_PATH)

    results = {}
    all_problems = []

    for label, path in JOB_FILES.items():
        with open(path, encoding="utf-8") as f:
            job_text = f.read()

        print(f"=== {label} を分析中... ===")
        result = analyze(job_text, profile)
        results[label] = result

        problems = verify_quotes_exist_in_job_text(result, job_text, label)
        all_problems.extend(problems)

        print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))
        print()

    print("=== 引用の実在検証 ===")
    if all_problems:
        for p in all_problems:
            print("NG:", p)
    else:
        print("OK: すべてのjob_posting_quoteが求人票本文に実在しました。")

    print()
    print("=== application_decision 比較 ===")
    decisions = {label: r.application_decision.recommendation for label, r in results.items()}
    for label, rec in decisions.items():
        print(f"{label}: {rec}")

    values = list(decisions.values())
    if len(set(values)) > 1:
        print("OK: 2件でapplication_decisionが分かれました。")
    else:
        print("NOTE: 2件のapplication_decisionは同じ結果でした。")

    if all_problems:
        sys.exit(1)


if __name__ == "__main__":
    main()

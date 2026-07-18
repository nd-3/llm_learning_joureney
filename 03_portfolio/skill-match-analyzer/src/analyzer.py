"""skill-match-analyzer のコアロジック。

求人票テキストとスキルプロファイルを突き合わせ、Claude Haiku 4.5 + Pydanticの
構造化出力で分析結果(SkillMatchAnalysis)を返す。FastAPI(api.py)・CLI(本ファイルの
__main__)の両方からこのモジュールの関数を呼び出す。
"""

import argparse
import json
import os
import sys

import anthropic
import yaml
from dotenv import load_dotenv

from schema import SkillMatchAnalysis

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PROFILE_PATH = os.path.join(BASE_DIR, "skill_profile.yaml")

# 使用するLLMモデル
CLAUDE_MODEL = "claude-haiku-4-5"

# 求人票に書かれていない要件を創作しないこと、根拠は必ず原文からの引用であることを
# 明示的に指示する。matched_skills.evidenceの構造(引用+プロファイル対応項目)と、
# application_decisionがpreferencesとの整合も考慮する点も併せて指示する。
SYSTEM_PROMPT = """あなたは求人票とスキルプロファイルを突き合わせて分析するキャリアアドバイザーです。
以下のルールを厳守してください。

- 求人票に書かれていない要件を創作しないこと。求人票の原文に書かれている内容のみを根拠にすること。
- matched_skills の根拠(evidence)には、必ず求人票からの短い引用(job_posting_quote)と、
  それに対応するスキルプロファイル側の項目(profile_reference)の両方を含めること。
- gaps の根拠(reason)も、求人票の記述に基づくこと。
- application_decision は、スキル面での適合度だけでなく、スキルプロファイルのpreferences
  (目指す方向性・避けたい方向性・重視条件)との整合性も考慮して判断すること。
"""


def load_api_key() -> None:
    """.envからANTHROPIC_API_KEYを読み込み、未設定の場合はエラー終了する。"""
    load_dotenv()
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("エラー: ANTHROPIC_API_KEYが.envに設定されていません。")


def load_profile(path: str = DEFAULT_PROFILE_PATH) -> dict:
    """スキルプロファイルのYAMLファイルを読み込む。"""
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_user_message(job_text: str, profile: dict) -> str:
    """スキルプロファイルと求人票を、LLMに渡すユーザーメッセージに組み立てる。"""
    profile_text = yaml.safe_dump(profile, allow_unicode=True, sort_keys=False)
    return f"""# スキルプロファイル
{profile_text}

# 求人票
{job_text}

上記のスキルプロファイルと求人票を突き合わせて分析してください。
"""


def analyze(job_text: str, profile: dict) -> SkillMatchAnalysis:
    """求人票テキストとスキルプロファイルを突き合わせ、構造化された分析結果を返す。"""
    client = anthropic.Anthropic()

    response = client.messages.parse(
        model=CLAUDE_MODEL,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": build_user_message(job_text, profile)}],
        output_format=SkillMatchAnalysis,
    )

    return response.parsed_output


def parse_args() -> argparse.Namespace:
    """コマンドライン引数を解析する(求人票テキストファイルのパスを受け取る)。"""
    parser = argparse.ArgumentParser(description="求人票とスキルプロファイルを突き合わせて分析する")
    parser.add_argument("job_text_path", help="求人票テキストファイルのパス")
    parser.add_argument(
        "--profile",
        default=DEFAULT_PROFILE_PATH,
        help=f"スキルプロファイルYAMLのパス(デフォルト: {DEFAULT_PROFILE_PATH})",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.job_text_path):
        sys.exit(f"エラー: 指定された求人票ファイルが見つかりません: {args.job_text_path}")
    if not os.path.exists(args.profile):
        sys.exit(f"エラー: 指定されたスキルプロファイルが見つかりません: {args.profile}")

    load_api_key()

    with open(args.job_text_path, encoding="utf-8") as f:
        job_text = f.read()
    profile = load_profile(args.profile)

    result = analyze(job_text, profile)
    print(json.dumps(result.model_dump(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

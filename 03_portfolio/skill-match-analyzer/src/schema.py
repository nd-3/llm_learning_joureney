"""analyzer.py / api.py が共有する、分析結果の出力スキーマ(Pydantic)。

詳細な設計意図は docs/requirements.md の「出力スキーマ案」を参照。
"""

from typing import Literal

from pydantic import BaseModel, Field


class Evidence(BaseModel):
    """matched_skillsの根拠。求人票からの引用とプロファイル側の対応項目のペアで持つ。"""

    job_posting_quote: str = Field(description="求人票からの短い引用(原文そのまま)")
    profile_reference: str = Field(description="対応するスキルプロファイル側の項目(例: skillsの該当エントリ)")


class MatchedSkill(BaseModel):
    """求人票の要件と合致しているスキル。"""

    skill: str = Field(description="合致したスキル名")
    evidence: Evidence = Field(description="根拠(求人票からの引用とプロファイル側の対応項目のペア)")


class SkillGap(BaseModel):
    """求人票の要件に対して不足している、または経験が浅いスキル。

    severityの定義:
    - critical: 求人票が必須(must-have)として明記している要件が欠落している
    - moderate: 必須ではないが、あった方が望ましい(nice-to-have)要件の経験が浅い、または不足している
    - minor: 影響の小さい、些末なスキルの不足
    """

    skill: str = Field(description="不足している、または経験が浅いスキル名")
    severity: Literal["critical", "moderate", "minor"] = Field(description="ギャップの深刻度(クラスdocstring参照)")
    reason: str = Field(description="なぜギャップと判断したか")


class InterviewQuestion(BaseModel):
    """このギャップ・経歴から想定される面談質問。"""

    question: str = Field(description="想定される面談質問")
    intent: str = Field(description="面談官がこの質問で何を確認しようとしているか")


class ApplicationDecision(BaseModel):
    """マッチ度・ギャップを踏まえた応募判断。

    スキル面での適合度だけでなく、スキルプロファイルのpreferences
    (目指す方向性・避けたい方向性・重視条件)との整合性も考慮して判断する。
    """

    recommendation: Literal["apply", "consider", "skip"] = Field(
        description="応募判断(apply=応募推奨, consider=要検討, skip=非推奨)"
    )
    reasoning: str = Field(description="この判断に至った理由(スキル適合度と志向との整合の両方に触れること)")


class SkillMatchAnalysis(BaseModel):
    """求人票とスキルプロファイルの突き合わせ結果。"""

    match_score: int = Field(
        ge=0,
        le=100,
        description="マッチ度(0〜100の整数)。絶対的な採用可能性の予測ではなく、"
        "同一プロファイル内での求人票同士の相対比較用の指標。",
    )
    match_summary: str = Field(description="マッチ度の根拠を簡潔にまとめた文章")
    matched_skills: list[MatchedSkill] = Field(description="求人票の要件と合致しているスキルの一覧")
    gaps: list[SkillGap] = Field(description="不足している、または経験が浅いスキルの一覧")
    interview_questions: list[InterviewQuestion] = Field(description="想定される面談質問の一覧")
    application_decision: ApplicationDecision = Field(description="応募判断とその理由")

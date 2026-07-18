"""SkillMatchAnalysis(schema.py)のバリデーションテスト。"""

import pytest
from pydantic import ValidationError

from schema import (
    ApplicationDecision,
    Evidence,
    InterviewQuestion,
    MatchedSkill,
    SkillGap,
    SkillMatchAnalysis,
)


def _build_analysis(match_score: int) -> SkillMatchAnalysis:
    """match_score以外は固定値で埋めた、有効なSkillMatchAnalysisを組み立てる。"""
    return SkillMatchAnalysis(
        match_score=match_score,
        match_summary="テスト用の要約",
        matched_skills=[
            MatchedSkill(
                skill="Python",
                evidence=Evidence(
                    job_posting_quote="Python実務経験2年以上",
                    profile_reference="skills: Python(intermediate, 1年)",
                ),
            )
        ],
        gaps=[SkillGap(skill="AWS", severity="moderate", reason="求人票はAWS運用経験を求めているが実務経験なし")],
        interview_questions=[
            InterviewQuestion(question="AWSの実務経験はありますか?", intent="クラウド運用経験の有無を確認")
        ],
        application_decision=ApplicationDecision(recommendation="consider", reasoning="テスト用の理由"),
    )


@pytest.mark.parametrize("match_score", [0, 50, 100])
def test_match_score_within_valid_range_is_accepted(match_score):
    analysis = _build_analysis(match_score)
    assert analysis.match_score == match_score


@pytest.mark.parametrize("match_score", [-1, 101])
def test_match_score_out_of_range_is_rejected(match_score):
    with pytest.raises(ValidationError):
        _build_analysis(match_score)


def test_gap_severity_must_be_one_of_the_three_defined_values():
    with pytest.raises(ValidationError):
        SkillGap(skill="AWS", severity="urgent", reason="無効なseverityの例")


def test_application_decision_recommendation_must_be_valid():
    with pytest.raises(ValidationError):
        ApplicationDecision(recommendation="maybe", reasoning="無効なrecommendationの例")

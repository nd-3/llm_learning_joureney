# 要件定義書

## プロダクト名

skill-match-analyzer

## 目的

求人票・案件票のテキストを自分のスキルプロファイルと突き合わせ、マッチ度と根拠・合致スキル・ギャップ・想定面談質問・応募判断を構造化出力するツールを構築する。

## MVP スコープ

- 入力はテキストのみ（求人票・案件票の本文をそのまま貼り付け）
- スキルプロファイルはYAMLファイルで管理
- Claude API（Haiku 4.5）+ Pydanticによる構造化出力
- コアロジックはPython関数として実装し、その薄いラッパーとしてFastAPI（`POST /analyze` 1本のみ）を被せる

## スコープ外（MVPでは扱わない）

- PDF読み込み
- 求人サイトなどからのスクレイピング
- データベースへの永続化
- 認証・認可
- 画面UI（フロントエンド）

## スキルプロファイルの構造

`skill_profile.yaml`（実データ、`.gitignore`対象）は`skill_profile.example.yaml`（ダミー値、コミット対象）と同じ構造を持つ。主なフィールドは以下の通り。

- `name` / `summary` / `experience_years`: 基本情報
- `skills`: スキル名・習熟度（`expert` / `intermediate` / `beginner`）・経験年数のリスト
- `roles` / `education` / `certifications`: 経歴
- `preferences`: キャリアの志向性。応募判断（`application_decision`）は、スキル面の適合度だけでなく、この`preferences`との整合性も踏まえて行う
  - `desired_direction`: 目指す方向性（今後伸ばしたい・携わりたい領域）
  - `avoided_direction`: 避けたい方向性（担当したくない業務・環境）
  - `valued_conditions`: 重視する条件（働き方・裁量・チーム体制など）

## 出力スキーマ案（Pydantic）

分析結果は以下のPydanticモデルで構造化する。フィールドは英語のsnake_case、`description`に日本語で説明を持たせる。

```python
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
        description="マッチ度(0〜100の整数)。絶対的な採用可能性の予測ではなく、同一プロファイル内での求人票同士の相対比較用の指標。",
    )
    match_summary: str = Field(description="マッチ度の根拠を簡潔にまとめた文章")
    matched_skills: list[MatchedSkill] = Field(description="求人票の要件と合致しているスキルの一覧")
    gaps: list[SkillGap] = Field(description="不足している、または経験が浅いスキルの一覧")
    interview_questions: list[InterviewQuestion] = Field(description="想定される面談質問の一覧")
    application_decision: ApplicationDecision = Field(description="応募判断とその理由")
```

- `match_score`と`match_summary`が「マッチ度」と「根拠」に対応する
- `matched_skills`の各要素が持つ`evidence`（求人票からの引用 + プロファイル側の対応項目のペア）も、個別スキルレベルでの「根拠」に対応する
- `gaps`が「ギャップ」、`interview_questions`が「想定面談質問」、`application_decision`が「応募判断」に対応する

## 技術スタック

- 言語: Python
- LLM: Claude Haiku 4.5（Anthropic API、`anthropic`公式SDK）
- 構造化出力: Pydantic（`client.messages.parse()` + `output_format`）
- プロファイル管理: YAML
- Web API: FastAPI（`POST /analyze` 1本のみ）

## 成功の定義

実在の求人票テキスト1件を入力すると、上記スキーマに完全準拠した分析結果（`SkillMatchAnalysis`としてパース可能なJSON）が返ってくること。

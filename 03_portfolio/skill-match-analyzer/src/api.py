"""skill-match-analyzer の薄いFastAPIラッパー。

エンドポイントは POST /analyze の1本のみ。求人票テキストを受け取り、
スキルプロファイル(skill_profile.yaml)と突き合わせた分析結果を返す。
分析ロジック自体は analyzer.py の analyze() 関数がすべて持っており、
このファイルはHTTP入出力の変換のみを行う。
"""

from fastapi import FastAPI
from pydantic import BaseModel

from analyzer import DEFAULT_PROFILE_PATH, analyze, load_api_key, load_profile
from schema import SkillMatchAnalysis

app = FastAPI(title="skill-match-analyzer")


class AnalyzeRequest(BaseModel):
    job_text: str


@app.post("/analyze", response_model=SkillMatchAnalysis)
def analyze_endpoint(request: AnalyzeRequest) -> SkillMatchAnalysis:
    load_api_key()
    profile = load_profile(DEFAULT_PROFILE_PATH)
    return analyze(request.job_text, profile)

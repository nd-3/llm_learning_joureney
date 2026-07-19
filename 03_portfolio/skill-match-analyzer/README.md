# skill-match-analyzer

求人票・案件票のテキストを自分のスキルプロファイルと突き合わせ、マッチ度・根拠・合致スキル・ギャップ・想定面談質問・応募判断を構造化出力するツールです。入力は求人票フォーマットに限らず、対象企業について収集した公開テキスト（採用ページのJD、技術スタック、スカウト/指名文など）を連結したものでも構いません。詳しい要件・出力スキーマは [docs/requirements.md](docs/requirements.md) を参照してください。

## 実行例

以下は**架空の求人票2件**(`examples/`)と**ダミーのスキルプロファイル**(`skill_profile.example.yaml`)を、実際にClaude Haiku 4.5で分析した結果です。企業名・求人内容ともに実在しません。

```bash
python examples/run_examples.py
```

### 比較: スキルは合うが、志向で判断が変わる例

| | LLMアプリケーションエンジニア(架空求人) | 組込みソフトウェアエンジニア(架空求人) |
|---|---|---|
| match_score | 72 | 45 |
| application_decision | **consider** | **skip** |

`examples/job_sample_embedded.txt`は、ダミープロファイルが持つスキル(C言語expert・5年の産業機器向け組込み開発経験)と非常によく合致する案件です。しかし、プロファイルの`preferences.avoided_direction`(「組込みファームウェア専業の案件に戻ることを避けたい」)と正面から対立するため、`match_score`はむしろ低く算出され、`application_decision`は`skip`(非推奨)と判断されました。

> 組込み求人の`application_decision.reasoning`(抜粋):
> 「スキル面では必須要件を満たしているものの、キャリア志向の不整合が決定的な問題です。…スキル適合度は高いものの、キャリア志向と避けたい方向性の両面で大きくズレており…応募は推奨されません。」

一方`examples/job_sample_llm.txt`は、スキル面では一部ギャップがあるものの、`preferences.desired_direction`(AI/LLM開発への転向)と強く合致するため`consider`(要検討)という判断になりました。「スキル適合度が高い方が必ずしも推奨されるとは限らない」ことが確認できます。

`matched_skills.evidence.job_posting_quote`がすべて求人票本文に実在すること(創作された引用でないこと)は、`examples/run_examples.py`内で機械的に検証しています。

### 実データでの実行(手元専用)

```bash
python src/analyzer.py path/to/実際の求人票.txt --profile skill_profile.yaml
```

## 主な機能(実装済みのみ記載)

- 求人票テキストとスキルプロファイル(YAML)を突き合わせ、Claude Haiku 4.5 + Pydanticの構造化出力で分析結果を生成(`src/analyzer.py`)
- コマンドラインから実行可能(求人票テキストファイルをパスで指定)
- `POST /analyze` 1本のみのFastAPIラッパー(`src/api.py`)
- 応募判断(`application_decision`)は、スキル適合度だけでなくプロファイルの`preferences`(志向)も考慮する設計を、架空データでの実行例で確認済み(下記「実行例」参照)

## 技術スタック

| 分類 | 技術 |
|---|---|
| 言語 | Python 3.10 |
| LLM | Claude Haiku 4.5(Anthropic API、`anthropic`公式SDK) |
| 構造化出力 | Pydantic(`client.messages.parse()` + `output_format`) |
| プロファイル管理 | YAML(PyYAML) |
| Web API | FastAPI |
| 環境変数管理 | python-dotenv |

## フォルダ構成

```text
skill-match-analyzer/
├── .env.example              # 環境変数のテンプレート(ダミー値)
├── docs/
│   └── requirements.md       # 要件定義書・出力スキーマ案
├── examples/                  # 架空データによる実行例(README「実行例」参照)
│   ├── job_sample_llm.txt
│   ├── job_sample_embedded.txt
│   └── run_examples.py        # 上記2件を実行し、引用の実在検証などを行うスクリプト
├── skill_profile.example.yaml  # スキルプロファイルのテンプレート(ダミー値)
├── requirements.txt
├── requirements-dev.txt
├── src/
│   ├── schema.py              # 出力スキーマ(Pydantic)
│   ├── analyzer.py            # コアロジック(analyze関数、CLIエントリポイント)
│   └── api.py                 # FastAPIラッパー(POST /analyze)
└── tests/
    ├── test_schema_validation.py
    └── test_profile_loading.py
```

`.env`(実際のAPIキー)と`skill_profile.yaml`(実データのスキルプロファイル)は`.gitignore`によりコミット対象外です。

## セットアップ

```bash
cd 03_portfolio/skill-match-analyzer

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定してください

cp skill_profile.example.yaml skill_profile.yaml
# skill_profile.yaml を自分の実データに書き換えてください
```

### CLIで実行

```bash
python src/analyzer.py path/to/job_posting.txt
```

### APIサーバーとして実行

```bash
uvicorn api:app --reload --app-dir src
```

## テスト

外部API(Anthropic)を呼ばない範囲で、出力スキーマのバリデーションとスキルプロファイル読み込みをpytestで検証しています。APIキーなしで実行できます。

```bash
pip install -r requirements-dev.txt
pytest -v
```

GitHub Actions(`.github/workflows/ci.yml`)で`push`/`pull_request`時に自動実行されます。

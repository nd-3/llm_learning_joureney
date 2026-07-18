# skill-match-analyzer

求人票・案件票のテキストを自分のスキルプロファイルと突き合わせ、マッチ度・根拠・合致スキル・ギャップ・想定面談質問・応募判断を構造化出力するツールです。詳しい要件・出力スキーマは [docs/requirements.md](docs/requirements.md) を参照してください。

## 実行例

<!-- TODO: 実際の求人票テキストで実行した結果をここに貼る -->

## 主な機能(実装済みのみ記載)

- 求人票テキストとスキルプロファイル(YAML)を突き合わせ、Claude Haiku 4.5 + Pydanticの構造化出力で分析結果を生成(`src/analyzer.py`)
- コマンドラインから実行可能(求人票テキストファイルをパスで指定)
- `POST /analyze` 1本のみのFastAPIラッパー(`src/api.py`)

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

"""QAデータセット(qa_dataset.json / qa_dataset_v2.json)の構造整合性テスト。"""

import json
import os

import pytest

EVALS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "evals")
DATASET_PATHS = [
    os.path.join(EVALS_DIR, "qa_dataset.json"),
    os.path.join(EVALS_DIR, "qa_dataset_v2.json"),
]
VALID_TYPES = {"single", "multi", "not_in_doc"}


def _load_dataset(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("path", DATASET_PATHS)
def test_dataset_has_25_questions(path):
    data = _load_dataset(path)
    assert len(data) == 25


@pytest.mark.parametrize("path", DATASET_PATHS)
def test_dataset_ids_are_sequential_from_1(path):
    data = _load_dataset(path)
    ids = [item["id"] for item in data]
    assert ids == list(range(1, 26))


@pytest.mark.parametrize("path", DATASET_PATHS)
def test_dataset_types_are_one_of_the_three_valid_types(path):
    data = _load_dataset(path)
    for item in data:
        assert item["type"] in VALID_TYPES


@pytest.mark.parametrize("path", DATASET_PATHS)
def test_expected_keywords_follow_type_rules(path):
    data = _load_dataset(path)
    for item in data:
        keywords = item["expected_keywords"]
        if item["type"] == "not_in_doc":
            assert keywords == []
        else:
            assert len(keywords) >= 1

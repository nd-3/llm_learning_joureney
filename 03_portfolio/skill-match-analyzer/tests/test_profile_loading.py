"""スキルプロファイル(YAML)読み込みと、example.yamlの構造整合性のテスト。

実データの skill_profile.yaml は .gitignore 対象で常に存在するとは限らないため、
リポジトリにコミットされている skill_profile.example.yaml を対象にテストする。
"""

import os

from analyzer import load_profile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAMPLE_PROFILE_PATH = os.path.join(PROJECT_ROOT, "skill_profile.example.yaml")

REQUIRED_TOP_LEVEL_KEYS = {
    "name",
    "summary",
    "experience_years",
    "skills",
    "roles",
    "education",
    "certifications",
    "preferences",
}
REQUIRED_PREFERENCES_KEYS = {"desired_direction", "avoided_direction", "valued_conditions"}
REQUIRED_SKILL_KEYS = {"name", "level"}
VALID_SKILL_LEVELS = {"expert", "intermediate", "beginner"}


def test_load_profile_returns_dict():
    profile = load_profile(EXAMPLE_PROFILE_PATH)
    assert isinstance(profile, dict)


def test_example_profile_has_required_top_level_keys():
    profile = load_profile(EXAMPLE_PROFILE_PATH)
    assert REQUIRED_TOP_LEVEL_KEYS.issubset(profile.keys())


def test_example_profile_preferences_has_required_keys():
    profile = load_profile(EXAMPLE_PROFILE_PATH)
    assert REQUIRED_PREFERENCES_KEYS.issubset(profile["preferences"].keys())


def test_example_profile_skills_have_name_and_valid_level():
    profile = load_profile(EXAMPLE_PROFILE_PATH)
    assert len(profile["skills"]) >= 1
    for skill in profile["skills"]:
        assert REQUIRED_SKILL_KEYS.issubset(skill.keys())
        assert skill["level"] in VALID_SKILL_LEVELS


def test_example_profile_valued_conditions_is_a_non_empty_list():
    profile = load_profile(EXAMPLE_PROFILE_PATH)
    valued_conditions = profile["preferences"]["valued_conditions"]
    assert isinstance(valued_conditions, list)
    assert len(valued_conditions) >= 1

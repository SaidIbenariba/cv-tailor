import pytest

from jobhunt.config import load_config

_YAML = """
search_terms: ["Data Scientist"]
locations: ["Morocco"]
boards: ["indeed", "linkedin"]
remote_only: true
results_per_term: 20
hours_old: 72
salary_min: 40000
exclude_keywords: ["unpaid"]
include_keywords: ["data"]
score_threshold: 50
fallback_recipient: null
cv_tex_path: "cv_said_ibenariba.tex"
country: "Morocco"
cv_skills: ["python", "pytorch"]
"""


def test_load_config_parses_yaml(tmp_path):
    p = tmp_path / "preferences.yaml"
    p.write_text(_YAML)
    cfg = load_config(p)
    assert cfg.search_terms == ["Data Scientist"]
    assert cfg.boards == ["indeed", "linkedin"]
    assert cfg.remote_only is True
    assert cfg.score_threshold == 50
    assert cfg.fallback_recipient is None


def test_load_config_rejects_missing_required_key(tmp_path):
    p = tmp_path / "preferences.yaml"
    p.write_text('search_terms: ["x"]\n')  # everything else missing
    with pytest.raises(ValueError, match="preferences.yaml"):
        load_config(p)


def test_load_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nope.yaml")

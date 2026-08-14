import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from ethics_filter.engine import (  # noqa: E402
    DEFAULT_AUDIT_PATH,
    MODULE_NAMES,
    get_constitution,
    load_constitutions,
)


@pytest.fixture
def constitutions():
    return load_constitutions()


@pytest.fixture
def constitution():
    return get_constitution("small-business-ethical")


@pytest.fixture
def audit_path(tmp_path):
    return tmp_path / "audit.jsonl"


@pytest.fixture
def sample_scores():
    """Scores for a mildly imperfect but broadly ethical decision."""
    return {
        "fairness": 90,
        "transparency": 85,
        "conscious-leadership": 80,
        "ethical-framework": 88,
        "compliance": 75,
    }


@pytest.fixture
def all_module_scores():
    return {name: 80.0 for name in MODULE_NAMES}

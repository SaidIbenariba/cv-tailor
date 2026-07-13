import pytest

from jobhunt.models import Config, JobRecord


@pytest.fixture
def cv_tex() -> str:
    return r"""
    \section{Profile}
    Data Scientist and AI Engineer with deep learning, PyTorch and NLP experience.
    \section{Technical Skills}
    Python, PySpark, Docker, PostgreSQL, FastAPI, Hugging Face.
    """


@pytest.fixture
def base_config() -> Config:
    return Config(
        search_terms=["Data Scientist"],
        locations=["Morocco"],
        boards=["indeed"],
        remote_only=False,
        results_per_term=10,
        hours_old=168,
        salary_min=None,
        exclude_keywords=["unpaid", "clearance required"],
        include_keywords=["data", "machine learning", "ai"],
        score_threshold=35,
        fallback_recipient=None,
        cv_tex_path="cv_said_ibenariba.tex",
        country="Morocco",
        cv_skills=[
            "python", "pytorch", "tensorflow", "nlp", "deep learning",
            "machine learning", "docker", "fastapi", "ai",
        ],
    )


def make_job(**overrides) -> JobRecord:
    base = dict(
        id="job-1",
        title="Data Scientist",
        company="Acme",
        location="Rabat, Morocco",
        is_remote=False,
        description="We need Python, deep learning and NLP for our data team.",
        url="https://example.com/job-1",
        salary_min=None,
        email=None,
        source="indeed",
        scraped_at="2026-05-19T00:00:00",
    )
    base.update(overrides)
    return JobRecord(**base)


@pytest.fixture
def job_factory():
    return make_job

import pandas as pd

from jobhunt import discover, score, store
from jobhunt.models import JobRecord


def _fake_scrape_df():
    return pd.DataFrame(
        [
            {
                "title": "Data Scientist",
                "company": "Acme",
                "location": "Rabat, Morocco",
                "job_url": "https://x.com/1",
                "description": "Python, deep learning, NLP for our data team",
                "is_remote": False,
                "min_amount": 45000,
                "emails": "jobs@acme.com",
                "site": "indeed",
                "date_posted": "2026-05-18",
            },
            {
                "title": "Barista",
                "company": "Cafe",
                "location": "Rabat",
                "job_url": "https://x.com/2",
                "description": "Make coffee",
                "is_remote": False,
                "min_amount": None,
                "emails": None,
                "site": "indeed",
                "date_posted": "2026-05-18",
            },
        ]
    )


def test_discover_normalizes_jobspy_rows(monkeypatch, base_config):
    monkeypatch.setattr(discover, "scrape_jobs", lambda **kw: _fake_scrape_df())
    jobs = discover.discover(base_config)
    assert all(isinstance(j, JobRecord) for j in jobs)
    ds = next(j for j in jobs if j.title == "Data Scientist")
    assert ds.email == "jobs@acme.com"
    assert ds.salary_min == 45000
    assert ds.url == "https://x.com/1"


def test_discover_passes_boolean_is_remote_to_jobspy(monkeypatch, base_config):
    # JobSpy's ScraperInput rejects is_remote=None; it must be a real bool.
    captured = {}

    def capture(**kw):
        captured.update(kw)
        return _fake_scrape_df()

    base_config.remote_only = False
    monkeypatch.setattr(discover, "scrape_jobs", capture)
    discover.discover(base_config)
    assert captured["is_remote"] is False
    assert isinstance(captured["is_remote"], bool)


def test_discover_passes_country_indeed(monkeypatch, base_config):
    # Without country_indeed, JobSpy's Indeed scraper defaults to the US.
    captured = {}
    monkeypatch.setattr(discover, "scrape_jobs",
                        lambda **kw: captured.update(kw) or _fake_scrape_df())
    base_config.country = "Morocco"
    discover.discover(base_config)
    assert captured["country_indeed"] == "Morocco"


def test_discover_continues_when_a_board_fails(monkeypatch, base_config):
    base_config.boards = ["indeed", "linkedin"]
    calls = {"n": 0}

    def flaky(**kw):
        calls["n"] += 1
        if kw.get("site_name") == ["linkedin"] or "linkedin" in str(kw):
            raise RuntimeError("blocked")
        return _fake_scrape_df()

    monkeypatch.setattr(discover, "scrape_jobs", flaky)
    jobs = discover.discover(base_config)
    assert len(jobs) > 0  # indeed results survived the linkedin failure


def test_discover_to_score_to_store_pipeline(monkeypatch, base_config):
    monkeypatch.setattr(discover, "scrape_jobs", lambda **kw: _fake_scrape_df())
    jobs = discover.discover(base_config)

    df = store.empty_frame()
    df = store.upsert(df, jobs)
    for _, row in df.iterrows():
        job = next(j for j in jobs if j.id == row["id"])
        ok, reason = score.hard_filter(job, base_config)
        if not ok:
            store.update_status(df, job.id, "FILTERED", FilterReason=reason)
        else:
            r = score.score_job(job, base_config)
            store.update_status(df, job.id, "SCORED", Score=r.score,
                                Matched=", ".join(r.matched))

    statuses = set(df["Status"])
    assert "SCORED" in statuses      # Data Scientist passed
    assert "FILTERED" in statuses    # Barista filtered out

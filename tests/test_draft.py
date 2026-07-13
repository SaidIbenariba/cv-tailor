import json

from jobhunt import draft, store
from jobhunt.models import ScoreResult


class DummyCV:
    """Stand-in CVProvider that returns a fixed (or no) attachment."""

    def __init__(self, path=None):
        self._path = path

    def get_attachment(self, job):
        return self._path


def test_render_email_mentions_company_and_matched_skills(job_factory):
    job = job_factory(title="ML Engineer", company="Globex")
    email = draft.render_email(job, ScoreResult(score=80, matched=["python", "nlp"]))
    assert "Globex" in email.subject
    assert "ML Engineer" in email.body
    assert "python" in email.body.lower()


def _scored_df(job_factory, **job_kw):
    df = store.empty_frame()
    df = store.upsert(df, [job_factory(**job_kw)])
    return store.update_status(df, job_kw.get("id", "job-1"), "SCORED", Score=80)


def test_draft_marks_needs_manual_when_no_email(tmp_path, base_config, job_factory):
    df = _scored_df(job_factory, id="job-1", email=None)
    df = draft.draft_jobs(df, base_config, DummyCV(), tmp_path)
    assert df.loc[df["id"] == "job-1", "Status"].iloc[0] == "NEEDS_MANUAL"
    assert not any(tmp_path.iterdir())


def test_draft_writes_outbox_and_sets_DRAFTED(tmp_path, base_config, job_factory):
    cv = tmp_path / "cv.pdf"
    cv.write_bytes(b"%PDF-1.4 fake")
    df = _scored_df(job_factory, id="job-1", email="jobs@globex.com")
    df = draft.draft_jobs(df, base_config, DummyCV(cv), tmp_path)

    assert df.loc[df["id"] == "job-1", "Status"].iloc[0] == "DRAFTED"
    job_dirs = [p for p in tmp_path.iterdir() if p.is_dir()]
    assert len(job_dirs) == 1
    meta = json.loads((job_dirs[0] / "meta.json").read_text())
    assert meta["recipient"] == "jobs@globex.com"
    assert meta["attachment"].endswith("cv.pdf")
    assert (job_dirs[0] / "email.md").exists()


def test_draft_skips_below_threshold(tmp_path, base_config, job_factory):
    df = store.empty_frame()
    df = store.upsert(df, [job_factory(id="low", email="a@b.com")])
    df = store.update_status(df, "low", "SCORED", Score=5)
    df = draft.draft_jobs(df, base_config, DummyCV(), tmp_path)
    # Below threshold stays SCORED, no outbox entry.
    assert df.loc[df["id"] == "low", "Status"].iloc[0] == "SCORED"
    assert not any(tmp_path.iterdir())


def test_draft_uses_fallback_recipient_when_set(tmp_path, base_config, job_factory):
    base_config.fallback_recipient = "me@example.com"
    df = _scored_df(job_factory, id="job-1", email=None)
    df = draft.draft_jobs(df, base_config, DummyCV(), tmp_path)
    assert df.loc[df["id"] == "job-1", "Status"].iloc[0] == "DRAFTED"

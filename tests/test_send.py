import json

import pytest

from jobhunt import send, store


def _approved(tmp_path, job_factory, recipient="jobs@acme.com", attach=True):
    df = store.empty_frame()
    df = store.upsert(df, [job_factory(id="job-1", email=recipient)])
    df = store.update_status(df, "job-1", "APPROVED", Recipient=recipient)
    d = tmp_path / "acme-job-1"
    d.mkdir()
    (d / "email.md").write_text("Subject: Application: DS at Acme\n\nHello team")
    att = None
    if attach:
        att = tmp_path / "cv.pdf"
        att.write_bytes(b"%PDF-1.4 x")
    (d / "meta.json").write_text(json.dumps({
        "job_id": "job-1", "recipient": recipient,
        "subject": "Application: DS at Acme",
        "attachment": str(att) if att else None, "url": "u",
    }))
    return df


def test_dry_run_sends_nothing_and_keeps_status(tmp_path, job_factory):
    df = _approved(tmp_path, job_factory)
    calls = []
    df = send.send_all(df, tmp_path, sender=lambda **k: calls.append(k), dry_run=True)
    assert calls == []
    assert df.loc[df["id"] == "job-1", "Status"].iloc[0] == "APPROVED"


def test_real_send_marks_SENT_and_calls_sender(tmp_path, job_factory):
    df = _approved(tmp_path, job_factory)
    calls = []
    df = send.send_all(df, tmp_path, sender=lambda **k: calls.append(k))
    assert len(calls) == 1
    assert calls[0]["recipient"] == "jobs@acme.com"
    row = df.loc[df["id"] == "job-1"].iloc[0]
    assert row["Status"] == "SENT"
    assert row["SentAt"]


def test_only_approved_rows_are_sent(tmp_path, job_factory):
    df = _approved(tmp_path, job_factory)
    df = store.upsert(df, [job_factory(id="other", email="x@y.com")])  # NEW
    calls = []
    send.send_all(df, tmp_path, sender=lambda **k: calls.append(k))
    assert len(calls) == 1


def test_sender_failure_aborts_without_marking_sent(tmp_path, job_factory):
    df = _approved(tmp_path, job_factory)

    def boom(**k):
        raise RuntimeError("SMTP auth failed")

    with pytest.raises(RuntimeError, match="SMTP auth"):
        send.send_all(df, tmp_path, sender=boom)
    assert df.loc[df["id"] == "job-1", "Status"].iloc[0] == "APPROVED"

"""Render application emails into an outbox for human review.

Nothing is sent here. Each drafted job becomes outbox/<slug>/ containing
email.md (editable) and meta.json (recipient + attachment for the send step).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from jobhunt.cv import CVProvider
from jobhunt.models import Config, JobRecord, ScoreResult

_SLUG = re.compile(r"[^a-z0-9]+")


@dataclass
class Email:
    subject: str
    body: str


def _slug(job: JobRecord) -> str:
    raw = f"{job.company}-{job.title}-{job.id}".lower()
    return _SLUG.sub("-", raw).strip("-")[:80]


def render_email(job: JobRecord, score: ScoreResult) -> Email:
    skills = ", ".join(score.matched[:8]) or "my background"
    subject = f"Application: {job.title} at {job.company}"
    body = (
        f"Dear {job.company} Hiring Team,\n\n"
        f"I'm writing to apply for the {job.title} position. "
        f"My experience aligns closely with this role, particularly in "
        f"{skills}.\n\n"
        f"My CV is attached. I'd welcome the chance to discuss how I can "
        f"contribute to your team.\n\n"
        f"Job reference: {job.url}\n\n"
        f"Best regards,\n"
        f"Said Ibenariba\n"
        f"saidibenariba@gmail.com | +212 684-419-392\n"
    )
    return Email(subject=subject, body=body)


def _job_from_row(row: pd.Series) -> JobRecord:
    return JobRecord(
        id=str(row["id"]),
        title=str(row["title"]),
        company=str(row["company"]),
        location=str(row.get("location") or ""),
        is_remote=bool(row.get("is_remote")),
        description=str(row.get("description") or ""),
        url=str(row.get("url") or ""),
        salary_min=None,
        email=(None if pd.isna(row.get("email")) else row.get("email")),
        source=str(row.get("source") or ""),
        scraped_at=str(row.get("scraped_at") or ""),
    )


def draft_jobs(
    df: pd.DataFrame,
    config: Config,
    cv_provider: CVProvider,
    outbox_dir: str | Path,
) -> pd.DataFrame:
    """Draft every SCORED job at/above threshold. Mutates and returns df."""
    from jobhunt import store

    outbox_dir = Path(outbox_dir)
    outbox_dir.mkdir(parents=True, exist_ok=True)

    scored = df[df["Status"] == "SCORED"]
    for idx in scored.index:
        row = df.loc[idx]
        score_val = int(row["Score"]) if not pd.isna(row["Score"]) else 0
        if score_val < config.score_threshold:
            continue  # leave as SCORED; below the bar to draft

        job = _job_from_row(row)
        recipient = job.email or config.fallback_recipient
        if not recipient:
            store.update_status(
                df, job.id, "NEEDS_MANUAL",
                FilterReason="no contact email - apply via the job URL",
                Recipient=pd.NA,
            )
            continue

        matched_raw = row.get("Matched")
        matched_str = "" if pd.isna(matched_raw) else str(matched_raw)
        result = ScoreResult(
            score=score_val,
            matched=[m for m in matched_str.split(", ") if m],
        )
        email = render_email(job, result)

        job_dir = outbox_dir / _slug(job)
        job_dir.mkdir(parents=True, exist_ok=True)
        (job_dir / "email.md").write_text(
            f"Subject: {email.subject}\n\n{email.body}", encoding="utf-8"
        )

        attachment = cv_provider.get_attachment(job)
        meta = {
            "job_id": job.id,
            "recipient": recipient,
            "subject": email.subject,
            "attachment": str(attachment) if attachment else None,
            "url": job.url,
        }
        (job_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

        store.update_status(df, job.id, "DRAFTED", Recipient=recipient)

    return df

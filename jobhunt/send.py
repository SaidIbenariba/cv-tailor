"""Send APPROVED applications via Gmail SMTP.

`sender` is injected so the orchestration is unit-tested without a network.
Any sender failure (auth, connection) aborts the run immediately and nothing
is marked SENT, so a re-run resumes cleanly.
"""

from __future__ import annotations

import json
import logging
import smtplib
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

import pandas as pd

from jobhunt import store

log = logging.getLogger(__name__)


def gmail_sender(address: str, app_password: str):
    """Build a sender callable bound to a Gmail SMTP-SSL session."""

    def _send(*, recipient, subject, body, attachment):
        msg = EmailMessage()
        msg["From"] = address
        msg["To"] = recipient
        msg["Subject"] = subject
        msg.set_content(body)
        if attachment:
            data = Path(attachment).read_bytes()
            msg.add_attachment(
                data, maintype="application", subtype="pdf",
                filename=Path(attachment).name,
            )
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(address, app_password)
            smtp.send_message(msg)

    return _send


def send_all(df: pd.DataFrame, outbox_dir, sender, dry_run: bool = False) -> pd.DataFrame:
    outbox_dir = Path(outbox_dir)
    approved = df[df["Status"] == "APPROVED"]

    for idx in approved.index:
        job_id = str(df.loc[idx, "id"])
        job_dir = _find_dir(outbox_dir, job_id)
        if job_dir is None:
            log.warning("no outbox folder for approved job %s; skipping", job_id)
            continue

        meta = json.loads((job_dir / "meta.json").read_text())
        body = (job_dir / "email.md").read_text()

        if dry_run:
            log.info("[dry-run] would email %s (%s)", meta["recipient"], meta["subject"])
            continue

        sender(
            recipient=meta["recipient"],
            subject=meta["subject"],
            body=body,
            attachment=meta.get("attachment"),
        )
        store.update_status(
            df, job_id, "SENT",
            SentAt=datetime.now(timezone.utc).isoformat(),
        )

    return df


def _find_dir(outbox_dir: Path, job_id: str) -> Path | None:
    if not outbox_dir.exists():
        return None
    for d in outbox_dir.iterdir():
        if d.is_dir() and (d / "meta.json").exists():
            meta = json.loads((d / "meta.json").read_text())
            if str(meta.get("job_id")) == job_id:
                return d
    return None

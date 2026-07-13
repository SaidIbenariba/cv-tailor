"""Excel persistence. `data/jobs.xlsx` is the pipeline's single source of truth.

The Status column is the state machine:
    NEW -> FILTERED | SCORED -> DRAFTED -> APPROVED -> SENT | NEEDS_MANUAL | ERROR
"""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from jobhunt.models import JobRecord

# Job fields first, then pipeline-managed columns.
_JOB_FIELDS = [
    "id", "title", "company", "location", "is_remote",
    "url", "salary_min", "email", "source", "scraped_at", "description",
]
_PIPELINE_FIELDS = [
    "Status", "Score", "Matched", "Missing", "FilterReason", "Recipient", "SentAt",
]
COLUMNS = _JOB_FIELDS + _PIPELINE_FIELDS


def empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def load_sheet(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return empty_frame()
    df = pd.read_excel(path, dtype={"id": str})
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[COLUMNS]


def upsert(df: pd.DataFrame, records: list[JobRecord]) -> pd.DataFrame:
    """Append jobs whose id is not already present. Existing rows untouched."""
    existing = set(df["id"].astype(str)) if len(df) else set()
    new_rows = []
    for rec in records:
        if str(rec.id) in existing:
            continue
        existing.add(str(rec.id))
        row = {c: pd.NA for c in COLUMNS}
        row.update(asdict(rec))
        row["Status"] = "NEW"
        new_rows.append(row)
    if not new_rows:
        return df
    additions = pd.DataFrame(new_rows, columns=COLUMNS)
    if df.empty:
        return additions
    return pd.concat([df, additions], ignore_index=True)


def update_status(
    df: pd.DataFrame, job_id: str, status: str, **fields
) -> pd.DataFrame:
    mask = df["id"].astype(str) == str(job_id)
    df.loc[mask, "Status"] = status
    for key, value in fields.items():
        df.loc[mask, key] = value
    return df


def save_sheet(df: pd.DataFrame, path: str | Path) -> None:
    """Atomic write: build a temp file, then replace, so a crash never
    leaves a half-written workbook."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df[COLUMNS].to_excel(tmp, index=False)
    os.replace(tmp, path)

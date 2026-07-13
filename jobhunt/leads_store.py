"""Excel persistence for leads. `data/leads.xlsx` is the source of truth for leads.

The Status column is the state machine:
    NEW -> MESSAGED -> CONNECTED -> INTERVIEW
"""

from __future__ import annotations

import os
from dataclasses import asdict
from pathlib import Path

import pandas as pd

from jobhunt.models import LeadRecord

_LEAD_FIELDS = [
    "id", "name", "org", "title", "discovery_source", 
    "context", "user_hook", "linkedin_url", "social_url",
]
_PIPELINE_FIELDS = ["Status", "RelatedJobs"]
COLUMNS = _LEAD_FIELDS + _PIPELINE_FIELDS


def empty_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=COLUMNS)


def load_leads(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        return empty_frame()
    df = pd.read_excel(path, dtype={"id": str})
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    return df[COLUMNS]


def upsert_leads(df: pd.DataFrame, records: list[LeadRecord]) -> pd.DataFrame:
    """Append leads whose id is not already present. Existing rows untouched."""
    existing = set(df["id"].astype(str)) if len(df) else set()
    new_rows = []
    for rec in records:
        if str(rec.id) in existing:
            continue
        existing.add(str(rec.id))
        row = {c: pd.NA for c in COLUMNS}
        
        rec_dict = asdict(rec)
        # Map dataclass fields to Excel columns
        rec_dict["RelatedJobs"] = ", ".join(rec_dict.pop("related_jobs", []))
        rec_dict["Status"] = rec_dict.pop("status", "NEW")
            
        row.update(rec_dict)
        new_rows.append(row)
        
    if not new_rows:
        return df
    additions = pd.DataFrame(new_rows, columns=COLUMNS)
    if df.empty:
        return additions
    return pd.concat([df, additions], ignore_index=True)


def save_leads(df: pd.DataFrame, path: str | Path) -> None:
    """Atomic write."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    df[COLUMNS].to_excel(tmp, index=False)
    os.replace(tmp, path)

"""Job discovery via the python-jobspy library.

One scrape_jobs call per (board) covering all search terms. Per-board failures
(rate limits, blocks) are logged and skipped so one bad board never aborts the
whole run. `scrape_jobs` is module-level so tests can monkeypatch it.
"""

from __future__ import annotations

import hashlib
import logging

import pandas as pd
from jobspy import scrape_jobs

from jobhunt.models import Config, JobRecord

log = logging.getLogger(__name__)


def _cell(row: pd.Series, key: str):
    val = row.get(key)
    if val is None or (not isinstance(val, (list,)) and pd.isna(val)):
        return None
    return val


def _job_id(row: pd.Series) -> str:
    url = _cell(row, "job_url")
    if url:
        return str(url)
    raw = f"{_cell(row,'title')}|{_cell(row,'company')}|{_cell(row,'location')}"
    return hashlib.sha1(raw.encode()).hexdigest()


def _email(row: pd.Series) -> str | None:
    val = _cell(row, "emails")
    if not val:
        return None
    if isinstance(val, list):
        return val[0] if val else None
    return str(val).split(",")[0].strip() or None

def _to_record(row: pd.Series, scraped_at: str) -> JobRecord:
    salary = _cell(row, "min_amount")
    return JobRecord(
        id=_job_id(row),
        title=str(_cell(row, "title") or ""),
        company=str(_cell(row, "company") or ""),
        location=str(_cell(row, "location") or ""),
        is_remote=bool(_cell(row, "is_remote")),
        description=str(_cell(row, "description") or ""),
        url=str(_cell(row, "job_url") or ""),
        salary_min=float(salary) if salary is not None else None,
        email=_email(row),
        source=str(_cell(row, "site") or ""),
        scraped_at=scraped_at,
    )


def discover(config: Config) -> list[JobRecord]:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    records: list[JobRecord] = []
    seen: set[str] = set()

    for board in config.boards:
        for term in config.search_terms:
            for loc in config.locations:
                # Indeed requires valid country strings; if we have a list, loop over them.
                # Other boards ignore country_indeed, but JobSpy still validates it.
                # We use 'worldwide' as a safe default for non-Indeed boards.
                if board == "indeed" and isinstance(config.country, list):
                    countries = config.country
                elif board == "indeed":
                    countries = [config.country]
                else:
                    countries = ["worldwide"]

                for ctry in countries:
                    try:
                        df = scrape_jobs(
                            site_name=[board],
                            search_term=term,
                            location=loc,
                            results_wanted=config.results_per_term,
                            hours_old=config.hours_old,
                            is_remote=bool(config.remote_only),
                            country_indeed=ctry,
                        )
                    except Exception as exc:  # noqa: BLE001 - board-level isolation
                        log.warning("board %s term %r failed: %s", board, term, exc)
                        continue
                    if df is None or len(df) == 0:
                        continue
                    for _, row in df.iterrows():
                        rec = _to_record(row, now)
                        if rec.id in seen:
                            continue
                        seen.add(rec.id)
                        records.append(rec)

    log.info("discovered %d unique jobs", len(records))
    return records

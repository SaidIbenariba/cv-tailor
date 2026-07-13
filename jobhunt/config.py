"""Load and validate preferences.yaml (+ .env for SMTP credentials)."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from jobhunt.models import Config

_REQUIRED = [
    "search_terms", "locations", "boards", "remote_only", "results_per_term",
    "hours_old", "salary_min", "exclude_keywords", "include_keywords",
    "score_threshold", "fallback_recipient", "cv_tex_path",
    "country", "cv_skills",
]


def load_config(path: str | Path = "preferences.yaml") -> Config:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"preferences file not found: {path}")

    data = yaml.safe_load(path.read_text()) or {}
    missing = [k for k in _REQUIRED if k not in data]
    if missing:
        raise ValueError(
            f"preferences.yaml is missing required keys: {', '.join(missing)}"
        )

    return Config(**{k: data[k] for k in _REQUIRED})


def load_smtp_credentials() -> tuple[str, str]:
    """Return (gmail_address, app_password) from .env / environment.

    Raised lazily by the send step so discovery/drafting work without creds.
    """
    load_dotenv()
    addr = os.environ.get("GMAIL_ADDRESS")
    pw = os.environ.get("GMAIL_APP_PASSWORD")
    if not addr or not pw:
        raise RuntimeError(
            "GMAIL_ADDRESS and GMAIL_APP_PASSWORD must be set in .env "
            "(copy .env.example). Use a Gmail App Password, not your login."
        )
    return addr, pw

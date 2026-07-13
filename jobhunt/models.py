"""Plain data containers shared across the pipeline.

Kept dependency-free (no pandas/yaml) so the pure-logic modules and their
tests import fast and in isolation.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class JobRecord:
    """One normalized job posting."""

    id: str
    title: str
    company: str
    location: str
    is_remote: bool
    description: str
    url: str
    salary_min: float | None
    email: str | None
    source: str
    scraped_at: str

    def text(self) -> str:
        """All free-text fields lowercased, for keyword matching."""
        return " ".join(
            x for x in (self.title, self.company, self.location, self.description) if x
        ).lower()


@dataclass
class Config:
    search_terms: list[str]
    locations: list[str]
    boards: list[str]
    remote_only: bool
    results_per_term: int
    hours_old: int | None
    salary_min: float | None
    exclude_keywords: list[str]
    include_keywords: list[str]
    score_threshold: int
    fallback_recipient: str | None
    cv_tex_path: str
    country: str | list[str]
    cv_skills: list[str]


@dataclass
class ScoreResult:
    score: int
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)


@dataclass
class LeadRecord:
    """One normalized networking lead (person or lab)."""

    id: str
    name: str
    org: str
    title: str
    discovery_source: str
    context: str
    user_hook: str
    linkedin_url: str | None = None
    social_url: str | None = None
    status: str = "NEW"
    related_jobs: list[str] = field(default_factory=list)

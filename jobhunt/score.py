"""Pure job matching logic: hard filters + curated-skill scoring.

Scoring matches a *curated* skill list (config.cv_skills, from the CV's skills
section) against the job text using word-boundary matching, so "retail" never
counts as the skill "ai". Score saturates: finding SATURATION distinct skills
in a posting is a perfect match, so a strong AI role lands 80-100 and an
unrelated role lands ~0. No I/O; fully deterministic and unit-tested.
"""

from __future__ import annotations

import re

from jobhunt.models import Config, JobRecord, ScoreResult

# Number of distinct CV skills in a posting that counts as a perfect match.
SATURATION = 6


def hard_filter(job: JobRecord, config: Config) -> tuple[bool, str]:
    """Return (passed, reason). reason is '' when passed is True."""
    text = job.text()

    if config.remote_only and not job.is_remote:
        return False, "remote-only required but job is not remote"

    if config.salary_min is not None and job.salary_min is not None:
        if job.salary_min < config.salary_min:
            return False, f"salary {job.salary_min} below floor {config.salary_min}"

    for kw in config.exclude_keywords:
        if kw.lower() in text:
            return False, f"matched exclude keyword: {kw}"

    if config.include_keywords:
        if not any(kw.lower() in text for kw in config.include_keywords):
            return False, "no include keyword present"

    return True, ""


def _skill_pattern(skill: str) -> re.Pattern:
    """Whole-token match; spaces become flexible whitespace.

    Boundaries use 'not alphanumeric' rather than \\b so skills ending in
    symbols (c++, node.js) still match correctly.
    """
    esc = re.escape(skill.lower()).replace(r"\ ", r"\s+")
    return re.compile(rf"(?<![a-z0-9]){esc}(?![a-z0-9])")


def score_job(job: JobRecord, config: Config) -> ScoreResult:
    """Score 0-100 from how many curated CV skills appear in the job text."""
    skills = [s.lower() for s in config.cv_skills]
    if not skills:
        return ScoreResult(score=0, matched=[], missing=[])

    text = job.text()
    matched = [s for s in skills if _skill_pattern(s).search(text)]
    missing = [s for s in skills if s not in matched]

    score = round(100 * min(len(matched), SATURATION) / SATURATION)
    return ScoreResult(score=score, matched=matched, missing=missing[:15])

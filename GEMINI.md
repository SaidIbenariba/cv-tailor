# Project Overview

`cv-tailor` is a personal job application workspace designed to automate the discovery, scoring, and preparation of job applications. It consists of three primary components:

1.  **`jobhunt` Python Package:** A custom pipeline that scrapes job boards (via [JobSpy]), filters and scores postings against a LaTeX CV, and drafts email applications for human review.
2.  **Master LaTeX CV (`cv_said_ibenariba.tex`):** The source of truth for the user's professional experience, designed for a single-column Data Scientist / AI Engineer profile.
3.  **Resume-Tailoring Skill:** A bundled Claude Code skill (located in `.claude/skills/resume-tailoring/`) for generating job-specific resume variants using LLMs.

The project prioritizes "human-in-the-loop" workflows over full automation to avoid violating job board Terms of Service.

## Architecture & Data Flow

-   **Job Metadata:** Stored in `data/jobs.xlsx`, which acts as the project's database.
-   **Configuration:** Managed via `preferences.yaml` (search terms, keywords, thresholds) and `.env` (Gmail credentials).
-   **Output:** Application drafts (email body + CV attachment) are generated in the `outbox/` directory.
-   **State Machine:** Jobs move through statuses in `jobs.xlsx`:
    `NEW` → `FILTERED` | `SCORED` → `DRAFTED` → `APPROVED` → `SENT` | `NEEDS_MANUAL`

## Building and Running

### Setup
1.  Initialize environment:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```
2.  Configure secrets: Copy `.env.example` to `.env` and provide a Gmail App Password.
3.  Configure preferences: Edit `preferences.yaml` for your target roles and locations.

### Workflow Commands
-   **Discover:** Scrape job boards and score postings.
    ```bash
    python -m jobhunt.cli discover
    ```
-   **Draft:** Generate email drafts in `outbox/` for jobs meeting the score threshold.
    ```bash
    python -m jobhunt.cli draft
    ```
-   **Send:** Send approved applications (Status must be `APPROVED` in `jobs.xlsx`).
    ```bash
    python -m jobhunt.cli send --dry-run  # Preview
    python -m jobhunt.cli send            # Actually send
    ```

### Testing
-   Run unit tests (I/O is mocked, suite runs in ~1s):
    ```bash
    python -m pytest
    ```

### CV Compilation
-   Compile the LaTeX CV (requires `pdflatex`):
    ```bash
    pdflatex cv_said_ibenariba.tex  # Run twice to resolve references
    ```

## Development Conventions

-   **Logic Isolation:** Pure logic (scoring, filtering, drafting) is kept in isolated modules and fully unit-tested in `tests/`.
-   **Data Containers:** `jobhunt/models.py` defines `JobRecord` and `Config` dataclasses used throughout the pipeline.
-   **CV Abstraction:** `jobhunt/cv.py` uses a `CVProvider` interface to decouple draft generation from CV building, facilitating future integration with tailored resumes.
-   **Truth-Preserving Tailoring:** All CV modifications (manual or automated) must follow the "truth-preserving" principle: reframe and emphasize to fit the job description, but never fabricate experience or dates.
-   **Git Management:** The project root is not a git repository. The `resume-tailoring` skill is a vendored git submodule under `.claude/skills/resume-tailoring/`.

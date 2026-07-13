# jobhunt — personal job discovery & application pipeline

Scrapes jobs from Indeed/LinkedIn/Google/Glassdoor (via [JobSpy]), saves them to
Excel, ranks each against your CV + preferences, and prepares **email**
applications for you to review before sending. No site automation, no bot
logins — that violates the boards' ToS and gets accounts banned.

[JobSpy]: https://github.com/speedyapply/JobSpy

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # then put your Gmail App Password in .env
$EDITOR preferences.yaml      # search terms, locations, filters, threshold
```

The Gmail password must be an **App Password** (myaccount.google.com/apppasswords,
2FA required), not your normal login.

## Workflow

```bash
.venv/bin/python -m jobhunt.cli discover     # scrape -> filter -> score -> data/jobs.xlsx
.venv/bin/python -m jobhunt.cli draft        # write outbox/<job>/ emails for good matches
# open data/jobs.xlsx, review DRAFTED rows, set Status = APPROVED for the ones to send
.venv/bin/python -m jobhunt.cli send --dry-run   # preview recipients/attachments
.venv/bin/python -m jobhunt.cli send             # actually send APPROVED jobs
```

`data/jobs.xlsx` is the single source of truth. The `Status` column is a state
machine you can hand-edit:

```
NEW → FILTERED | SCORED → DRAFTED → APPROVED → SENT
                                  ↘ NEEDS_MANUAL   (no contact email — apply via the URL)
```

Re-running `discover` is safe: known jobs (by URL) are skipped, their status
preserved.

## Honest limitations

- **Most LinkedIn/Indeed listings apply through the site, not by email.** Those
  have no contact address; the pipeline marks them `NEEDS_MANUAL` with the job
  URL so you can apply by hand. Email applications mostly work for company-direct
  / smaller postings that expose an address.
- **CV attachment needs LaTeX.** `cv.py` compiles `cv_said_ibenariba.tex` with
  `pdflatex`. If no TeX toolchain is installed, drafts are still produced but
  without the PDF attached (a warning is logged). Install MacTeX
  (`brew install --cask mactex-no-gui`) to enable attachments.
- Matching is keyword/rule based (offline, free, explainable) — it ranks, it
  doesn't read between the lines. Tune `include_keywords`, `exclude_keywords`
  and `score_threshold` in `preferences.yaml`.

## Extending

`jobhunt/cv.py` defines a `CVProvider` interface. `MasterCVProvider` attaches
one PDF to everything; a `TailoredCVProvider` can later call the vendored
`resume-tailoring` skill per job without changing `draft.py`.

## Tests

```bash
.venv/bin/python -m pytest -q
```

Pure logic (`score`, `store`, `draft`, `config`, `send`) is fully unit-tested;
JobSpy and SMTP are mocked, so the suite runs offline in ~1s.
# cv-tailor

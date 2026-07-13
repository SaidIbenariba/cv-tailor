# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is a personal CV/resume workspace for Said Ibenariba (Data Scientist & AI Engineer), not a software project. It has two distinct, loosely-coupled parts:

1. **The master LaTeX CV** — `cv_said_ibenariba.tex`, a single-column data-scientist CV.
2. **The bundled `resume-tailoring` skill** — a self-contained Claude Code skill (under `.claude/skills/resume-tailoring/`, with its own git repo) that generates job-tailored resumes from a markdown resume library in `resumes/`.

These two parts use different formats and toolchains. The LaTeX CV is the hand-maintained source of truth for the person's experience; the skill consumes/produces markdown + DOCX + PDF and expects a markdown library, which is a separate representation.

## Building the CV

```
pdflatex cv_said_ibenariba.tex   # run TWICE — second pass resolves tabularx/hyperref layout
```

The CV uses only standard `article` packages (geometry, xcolor, enumitem, titlesec, hyperref, tabularx, helvet). There is no Makefile or latexmk config.

**No LaTeX toolchain is installed on this machine** (`pdflatex`, `xelatex`, `latexmk`, `tectonic` are all absent). To compile you must first install one (e.g. MacTeX / `brew install --cask mactex-no-gui`, or use a container). Do not assume `pdflatex` works without checking.

## Editing the CV — structure conventions

The `.tex` file defines two custom macros that all content flows through; match these rather than hand-formatting:

- `\entry{title}{subtitle}{date}{location}` — a two-row header (bold title + muted right-aligned date; italic subtitle + muted right-aligned location). Pass empty `{}{}` for the trailing two args on Projects/Education entries that have no date/location.
- `\skill{label}{detail}` — currently unused in the body; the Technical Skills section uses a `tabularx` instead.

Section order is fixed and meaningful: Profile → Experience → Projects → Technical Skills → Education → Languages. Color scheme is intentionally all-black (`accent`/`dark` = `#000000`) with grey rules — keep it print-safe; don't reintroduce colored links (`hypersetup` is set to `colorlinks=false`).

When updating experience, keep dates and company names exact and factual. The skill's core principle (below) applies to manual edits too: reframe and emphasize, never fabricate.

## Tailored CVs — Awesome-CV template

For per-job tailored CVs Said now uses the **Awesome-CV** template
(`github.com/posquit0/Awesome-CV`), separate from the master `\entry`-macro CV.

- **Reusable base:** `resumes/_template_awesome-cv.tex`. To make a new one, copy to
  `resumes/cv_said_ibenariba_<company>.tex` and edit ONLY the `[[EDIT PER JOB]]`
  zones (`\position`, Profil paragraph, footer, reorder projects/skills to the JD).
  The template carries the full content library (1 experience + 4 projects +
  5 skill rows) — trim to fit one A4 page.
- **Toolchain:** XeLaTeX only (**NOT pdflatex**). Needs `awesome-cv.cls` + system
  fonts. Repo cloned at `Awesome-CV/`. No TeX toolchain on this machine — compile
  on Overleaf (import the repo, add the `.tex`, set compiler = XeLaTeX) or via
  Docker `texlive/texlive:latest` once the daemon is up.
- **Overleaf font fix (already applied in `Awesome-CV/awesome-cv.cls`):** master
  Awesome-CV calls `Source Sans 3`, which Overleaf's TeXLive lacks → fontspec
  "font cannot be found" + compile timeout. Patch `\setmainfont`/`\setsansfont`
  `Source Sans 3` → `Source Sans Pro` (Roboto stays).
- **Gotcha:** uploading a GitHub *blob* page saves HTML (`<!DOCTYPE html>` at line 7
  → "Missing `\begin{document}`"). Always grab `raw.githubusercontent.com`.
- The all-black, print-safe house style below still governs the original
  custom-class `.tex` CVs; Awesome-CV is a deliberate, separate styled track.

## The resume-tailoring skill

`resumes/` is the library directory the skill reads from. **It is currently empty** — the skill expects markdown resumes (`resumes/*.md`) and degrades gracefully but warns when the library is sparse. Before running a tailoring session, expect to either populate `resumes/` (e.g. a markdown export of the LaTeX CV) or accept limited-library mode.

The skill is invoked conversationally (e.g. "I want to apply for [Role] at [Company], here's the JD: …"), not via a command. Its full multi-phase workflow, checkpoints, matching/scoring algorithms, and multi-job batch mode are documented in `.claude/skills/resume-tailoring/skills/resume-tailoring/SKILL.md` and the sibling `*.md` files (`research-prompts.md`, `matching-strategies.md`, `branching-questions.md`, `multi-job-workflow.md`). Read SKILL.md before driving a tailoring session — the phase checkpoints (template approval, content-mapping approval, library-update decision) are mandatory user gates, not optional.

**Core principle (governs all generated content):** truth-preserving optimization. Maximize fit to the job; never invent experience, inflate seniority, or alter companies/dates. Reframing terminology and shifting emphasis is allowed; fabrication is not.

DOCX/PDF generation in the skill depends on the `docx`/`pdf` document skills being available; it falls back to markdown-only if not.

## The `resume-cover-letter` skill (vendored)

A second, separate skill lives at `.claude/skills/resume-cover-letter/SKILL.md`
(single self-contained file, vendored from `jezweb/claude-skills`). It writes a
resume/CV, a cover letter, or both, tailored to a specific role. It differs from
`resume-tailoring` in important ways — pick deliberately:

- **Markdown/ATS-first.** It explicitly refuses to generate `.docx`/`.pdf` and
  delivers clean markdown (`.md`/`.txt`) for pasting into Word/Docs/Canva. It is
  *not* the LaTeX `.tex` workflow used for the master CV / Capgemini-style apps.
- **Regional formats AU/NZ, US, UK** — not Morocco/France. For French-language
  postings, prefer the tailored `.tex` + the documented house style (no header
  rule, `•` separators, hyphen dates, `\labelitemi` bullet fix under babel-french).
- It *does* cover **cover letters** (which `resume-tailoring` explicitly excludes).

Both skills are invoked conversationally. Treat this directory as vendored
third-party code — change it upstream, not here, unless deliberately customizing.

## The `jobhunt` package

A Python job-search pipeline lives in `jobhunt/` (greenfield, added on top of
the CV workspace). It scrapes job boards via JobSpy, scores postings against the
LaTeX CV's keywords, and prepares **email** applications for human review — it
deliberately does no site automation/auto-login (ToS + ban risk).

- Run in the venv: `.venv/bin/python -m jobhunt.cli {discover,draft,send}`. Tests: `.venv/bin/python -m pytest -q`.
- `data/jobs.xlsx` is the single source of truth; the `Status` column is a
  hand-editable state machine (`NEW → FILTERED|SCORED → DRAFTED → APPROVED →
  SENT|NEEDS_MANUAL`). Commands are idempotent (dedupe by job URL).
- Pure logic (`score`, `store`, `draft`, `config`, `send`) is fully unit-tested
  with JobSpy/SMTP mocked — keep it I/O-free and TDD new behavior.
- `cv.py` reads `cv_said_ibenariba.tex`: extracts keywords for scoring and
  compiles it via `pdflatex` for the attachment. With no TeX toolchain it
  degrades to attachment-less drafts (warned, not fatal) — see the CV build note above.
- `CVProvider` in `cv.py` is the seam for future per-job tailoring via the
  vendored `resume-tailoring` skill; don't bypass it from `draft.py`.
- Design/spec: `~/.claude/plans/temporal-mapping-sphinx.md`. `data/` and
  `outbox/` are gitignored (contain personal application data).

## Git note

The repository root is **not** a git repo. The only git repo here is the vendored skill at `.claude/skills/resume-tailoring/.git` (upstream: `varunr89/resume-tailoring-skill`). Don't run git commands at the root expecting history, and treat the skill directory as vendored third-party code — change it upstream, not here, unless deliberately customizing.

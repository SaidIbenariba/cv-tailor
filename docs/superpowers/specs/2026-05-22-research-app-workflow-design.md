# Design Spec: Research Application Workflow

## Overview
An agent-orchestrated end-to-end pipeline designed for a Data Scientist Intern to discover, score, and apply to scientific research opportunities. The system automates repetitive tasks while maintaining a "human-in-the-loop" gate for low-scoring roles.

## Goals
- Automate the discovery of research-focused roles using the existing `jobhunt` package.
- Implement a **Hybrid Scoring Gate** that auto-processes strong matches and flags weak ones for manual intervention.
- Integrate the `resume-tailoring` skill to produce research-optimized CVs.
- Generate personalized Cover Letters tailored to scientific contexts.
- Maintain application state in `data/jobs.xlsx`.

## Architecture & Data Flow

### 1. Discovery & Filtering
- **Trigger:** Agent runs `python -m jobhunt.cli discover`.
- **Filtering:** The agent identifies jobs in `data/jobs.xlsx` with status `NEW`.

### 2. Hybrid Scoring Gate
- **Threshold:** 35% (defined in `preferences.yaml`).
- **Logic:**
  - **Score >= 35:** Automatically proceed to Phase 3.
  - **Score < 35:** Agent pauses and prompts user: "Low match score found. [Skip] or [Experience Discovery]?"
- **Experience Discovery:** If selected, triggers the interactive "Branching Discovery" from the `resume-tailoring` skill to surface missing research experience.

### 3. Tailoring & Generation
- **CV Tailoring:** Invokes `resume-tailoring` skill in "Express Mode" (or "Discovery Mode" if triggered by the gate).
- **Cover Letter Generation:** A new internal agent prompt generates a research-centric cover letter linking current skills to the lab's specific research mission.
- **Output Isolation:** Each application is saved in:
  `outbox/YYYY-MM-DD_[Company]_[Role]/`
  - `CV_Tailored.pdf` (or .tex/.md)
  - `Cover_Letter.md`
  - `Generation_Report.md`

### 4. Status Management
- Update `data/jobs.xlsx` status for each job:
  - `NEW` → `TAILORED` (after generation).
  - `NEW` → `SKIPPED` (if user rejects low score).

## Success Criteria
- [ ] Successfully refresh jobs from boards.
- [ ] Correctly identify and score `NEW` jobs.
- [ ] Trigger manual discovery session for scores < 35.
- [ ] Generate isolated folders for each application with tailored content.
- [ ] Update Excel state correctly to prevent duplicate work.

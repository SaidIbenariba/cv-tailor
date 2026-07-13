# Research Application Workflow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an agent-orchestrated pipeline for research-focused job applications.

**Architecture:** A Python bridge script manages job state in Excel, while a new Gemini CLI skill orchestrates discovery, hybrid scoring, and tailoring loops.

**Tech Stack:** Python (Pandas/JobSpy), Gemini CLI Skills.

---

### Task 1: Initialize the Agent Bridge

**Files:**
- Create: `jobhunt/agent_bridge.py`
- Test: `tests/test_agent_bridge.py`

- [ ] **Step 1: Write failing test for state retrieval**

```python
import pytest
import pandas as pd
import os
from jobhunt.agent_bridge import get_new_jobs

def test_get_new_jobs(tmp_path):
    xlsx_path = tmp_path / "jobs.xlsx"
    df = pd.DataFrame([
        {"id": "1", "title": "Job A", "status": "NEW", "company": "A", "location": "L", "url": "U", "description": "D"},
        {"id": "2", "title": "Job B", "status": "TAILORED", "company": "B", "location": "L", "url": "U", "description": "D"}
    ])
    df.to_excel(xlsx_path, index=False)
    
    new_jobs = get_new_jobs(str(xlsx_path))
    assert len(new_jobs) == 1
    assert new_jobs[0]["id"] == "1"
```

- [ ] **Step 2: Run test to verify failure**

Run: `pytest tests/test_agent_bridge.py`
Expected: `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Implement `get_new_jobs` and `update_job_status`**

```python
import pandas as pd
from typing import List, Dict

def get_new_jobs(xlsx_path: str) -> List[Dict]:
    try:
        df = pd.read_excel(xlsx_path)
        if "status" not in df.columns:
            return []
        return df[df["status"] == "NEW"].to_dict("records")
    except Exception:
        return []

def update_job_status(xlsx_path: str, job_id: str, status: str):
    df = pd.read_excel(xlsx_path)
    df.loc[df["id"] == job_id, "status"] = status
    df.to_excel(xlsx_path, index=False)
```

- [ ] **Step 4: Run test to verify pass**

Run: `pytest tests/test_agent_bridge.py`
Expected: `PASS`

- [ ] **Step 5: Commit**

```bash
git add jobhunt/agent_bridge.py tests/test_agent_bridge.py
git commit -m "feat: add agent bridge for job state management"
```

---

### Task 2: Create the Workflow Skill

**Files:**
- Create: `.agents/skills/research-app-workflow/SKILL.md`

- [ ] **Step 1: Write the SKILL.md content**

```markdown
---
name: research-app-workflow
description: Orchestrates discovery, hybrid scoring, and tailoring for research roles.
---

# Research Application Workflow

## Overview
This skill manages the end-to-end process of finding and applying for scientific research roles.

## Workflow:
1. **Refresh:** Run `python -m jobhunt.cli discover` to pull latest jobs.
2. **Fetch:** Use `jobhunt.agent_bridge.get_new_jobs` to identify `NEW` roles.
3. **Loop:** For each job:
   - **Score:** Calculate match score (use logic from `jobhunt/score.py`).
   - **Gate:**
     - If Score < 35: Ask user: "Score [X] is low. [Skip] or [Discovery Session]?"
     - If Score >= 35 or User chooses Discovery: Proceed to Tailoring.
   - **Tailor:**
     - Invoke `resume-tailoring` skill.
     - Use `.agents/skills/research-app-workflow/prompts/cover-letter.md` to generate a CL.
     - Save all outputs to `outbox/YYYY-MM-DD_Company_Role/`.
     - Update status to `TAILORED` via `update_job_status`.
```

- [ ] **Step 2: Commit**

```bash
git add .agents/skills/research-app-workflow/SKILL.md
git commit -m "feat: define research-app-workflow skill"
```

---

### Task 3: Cover Letter Template

**Files:**
- Create: `.agents/skills/research-app-workflow/prompts/cover-letter.md`

- [ ] **Step 1: Write the prompt template**

```markdown
# Research Cover Letter Prompt
You are helping a Data Scientist Intern apply for a scientific research position.
Context:
- User Background: [From CV]
- Job Description: [From JD]
- Research Mission: [From Company Research]

Instructions:
1. Write a formal 1-page cover letter.
2. Link the user's technical projects (e.g., NLP, LLMs) to the scientific outcomes mentioned in the JD.
3. Use a tone that is academic yet results-oriented.
4. Focus on "Model Development for Scientific Discovery".
```

- [ ] **Step 2: Commit**

```bash
git add .agents/skills/research-app-workflow/prompts/cover-letter.md
git commit -m "feat: add research cover letter prompt"
```

---

### Task 4: Final Verification

- [ ] **Step 1: Run full workflow dry-run**
- [ ] **Step 2: Verify folder isolation in `outbox/`**
- [ ] **Step 3: Verify Excel status update**

---
name: research-app-workflow
description: Orchestrates discovery, hybrid scoring, and tailoring for research roles.
---

# Research Application Workflow

## Overview
This skill manages the end-to-end process of finding and applying for scientific research roles. It automates the routine parts of the job search while ensuring that you have control over the final application content, especially for roles where the match might initially appear low.

## Workflow:
1. **Refresh:** Run `python -m jobhunt.cli discover` to pull the latest jobs from configured boards.
2. **Fetch:** Use the helper utility `jobhunt.agent_bridge.get_new_jobs` to identify all jobs currently in the `NEW` state.
3. **Loop:** For each `NEW` job:
   - **Score:** Calculate the match score using the logic defined in `jobhunt/score.py`.
   - **Gate:**
     - If the Score is below 35: Present the match findings to you. Ask: "Score [X] is low. [Skip] this job, or perform an [Experience Discovery] session to try to find additional research experience?"
     - If the Score is 35 or higher, or if you choose to perform discovery: Proceed to the Tailoring step.
   - **Tailor:**
     - Invoke the `resume-tailoring` skill to update your CV based on the job description.
     - Use the specific prompt in `.agents/skills/research-app-workflow/prompts/cover-letter.md` to generate a personalized cover letter.
     - Create an isolated folder for the application: `outbox/YYYY-MM-DD_[Company]_[Role]/`.
     - Save the tailored CV, the generated cover letter, and a generation report into this folder.
     - Update the job's status to `TAILORED` in the database using `jobhunt.agent_bridge.update_job_status`.

## Success Profile
A successful application in this workflow should bridge the gap between internship experience and the scientific research mission of the target organization, emphasizing model development, experimental rigor, and technical proficiency.

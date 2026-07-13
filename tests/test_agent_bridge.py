import pytest
import pandas as pd
import os
from jobhunt.agent_bridge import get_new_jobs

def test_get_new_jobs(tmp_path):
    xlsx_path = tmp_path / "jobs.xlsx"
    df = pd.DataFrame([
        {"id": "1", "title": "Job A", "Status": "NEW", "company": "A", "location": "L", "url": "U", "description": "D"},
        {"id": "2", "title": "Job B", "Status": "TAILORED", "company": "B", "location": "L", "url": "U", "description": "D"}
    ])
    df.to_excel(xlsx_path, index=False)
    
    new_jobs = get_new_jobs(str(xlsx_path))
    assert len(new_jobs) == 1
    assert new_jobs[0]["id"] == "1"

def test_update_job_status(tmp_path):
    from jobhunt.agent_bridge import update_job_status
    xlsx_path = tmp_path / "jobs.xlsx"
    df = pd.DataFrame([
        {"id": "1", "Status": "NEW"},
        {"id": "2", "Status": "NEW"}
    ])
    df.to_excel(xlsx_path, index=False)
    
    update_job_status(str(xlsx_path), "1", "TAILORED")
    
    df_updated = pd.read_excel(xlsx_path, dtype={"id": str})
    assert df_updated.loc[df_updated["id"] == "1", "Status"].iloc[0] == "TAILORED"
    assert df_updated.loc[df_updated["id"] == "2", "Status"].iloc[0] == "NEW"

import pandas as pd
from typing import List, Dict

def get_new_jobs(xlsx_path: str) -> List[Dict]:
    try:
        df = pd.read_excel(xlsx_path, dtype={"id": str})
        if "Status" not in df.columns:
            return []
        return df[df["Status"] == "NEW"].to_dict("records")
    except Exception:
        return []

def update_job_status(xlsx_path: str, job_id: str, status: str):
    df = pd.read_excel(xlsx_path, dtype={"id": str})
    df.loc[df["id"] == job_id, "Status"] = status
    df.to_excel(xlsx_path, index=False)

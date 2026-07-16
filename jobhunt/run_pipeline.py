# jobhunt/run_pipeline.py
import json
import logging
import os
import sys
from pathlib import Path
import yaml
import pandas as pd

from jobhunt.models import Config, JobRecord
from jobhunt.discover import discover
from jobhunt.score import hard_filter, score_job
from jobhunt.cv import TailoredCVProvider, MasterCVProvider

# Setup clean logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pipeline.log", encoding="utf-8")
    ]
)
log = logging.getLogger("pipeline_runner")

DB_PATH = Path("jobs_database.json")
PREFS_PATH = Path("preferences.yaml")

def load_config(yaml_path: Path) -> Config:
    if not yaml_path.exists():
        log.error(f"Configuration file not found at {yaml_path}")
        sys.exit(1)
    with open(yaml_path, "r", encoding="utf-8") as f:
        raw_data = yaml.safe_load(f)
    try:
        return Config(**raw_data)
    except TypeError as e:
        log.error(f"YAML keys do not match Config dataclass requirements: {e}")
        sys.exit(1)

def load_historical_database() -> dict[str, dict]:
    if not DB_PATH.exists():
        return {}
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {job["id"]: job for job in data}
    except Exception as e:
        log.warning(f"Failed to read historical database: {e}")
        return {}

def save_database(database: dict[str, dict]):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(list(database.values()), f, indent=4, ensure_ascii=False)
    log.info(f"Database saved. Total tracked jobs: {len(database)}")

def main():
    log.info("--- Starting Job Hunt Pipeline Run ---")
    
    config = load_config(PREFS_PATH)
    database = load_historical_database()
    log.info(f"Loaded {len(database)} historical postings.")

    # 1. Discover new postings
    raw_discovered = discover(config)
    
    new_scraps: list[JobRecord] = []
    for job in raw_discovered:
        if job.id not in database:
            new_scraps.append(job)

    log.info(f"Scraped {len(raw_discovered)} listings. Found {len(new_scraps)} brand new postings.")

    # Instantiate the dynamic CV Tailoring Engine
    # Swaps dynamically to TailoredCVProvider
    cv_engine = TailoredCVProvider(tex_path=config.cv_tex_path)

    actionable_leads = []
    
    # 2. Filter, Score and Tailor CVs
    for job in new_scraps:
        passed, reason = hard_filter(job, config)
        
        if not passed:
            log.info(f"Skipping {job.title} at {job.company} - Rejected: {reason}")
            database[job.id] = {
                "id": job.id,
                "title": job.title,
                "company": job.company,
                "url": job.url,
                "status": "REJECTED_FILTER",
                "rejection_reason": reason,
                "scraped_at": job.scraped_at
            }
            continue

        score_res = score_job(job, config)
        
        enriched_record = job.__dict__.copy()
        enriched_record.update({
            "score": score_res.score,
            "matched_skills": score_res.matched,
            "missing_skills": score_res.missing,
            "status": "MATCHED" if score_res.score >= config.score_threshold else "LOW_SCORE",
            "cv_attachment_path": None
        })

        # Compiles tailored PDF for applications above the threshold
        if score_res.score >= config.score_threshold:
            pdf_path = cv_engine.get_attachment(job)
            if pdf_path:
                enriched_record["cv_attachment_path"] = str(pdf_path)
                log.info(f"Tailored CV successfully generated at: {pdf_path}")
            
            actionable_leads.append(enriched_record)
        
        database[job.id] = enriched_record

    save_database(database)

    # 3. Generate summary report
    if actionable_leads:
        df = pd.DataFrame(actionable_leads)
        cols = ["score", "title", "company", "location", "matched_skills", "cv_attachment_path", "url"]
        df = df[[c for c in cols if c in df.columns] + [c for c in df.columns if c not in cols]]
        df.to_csv("discovered_jobs.csv", index=False)
        
        print(f"\n🚀 Tailoring Complete! Compiled {len(actionable_leads)} personalized CVs.")
        for i, lead in enumerate(sorted(actionable_leads, key=lambda x: x["score"], reverse=True)[:5], 1):
            print(f"  {i}. [{lead['score']}% Match] {lead['title']} at {lead['company']}")
            print(f"     PDF: {lead['cv_attachment_path']}")
            print(f"     Link: {lead['url']}\n")
    else:
        print("\n😴 No new matches scored high enough to trigger tailoring in this run.")

if __name__ == "__main__":
    main()

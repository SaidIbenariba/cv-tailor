"""Command-line entry point: `python -m jobhunt.cli {discover,draft,send,leads}`.

discover : scrape -> hard-filter -> score -> write data/jobs.xlsx
draft    : render outbox/ emails for SCORED jobs at/above threshold
send     : email APPROVED jobs (use --dry-run first)
leads    : manage networking leads (discover via scouts, draft ice-breakers)
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from jobhunt import score, store, leads_store
from jobhunt.config import load_config, load_smtp_credentials
from jobhunt.cv import MasterCVProvider
from jobhunt.discover import discover
from jobhunt.draft import draft_jobs
from jobhunt.send import gmail_sender, send_all
from jobhunt.models import LeadRecord
from jobhunt.outreach import generate_ice_breaker
from jobhunt.scouts.academic import AcademicScout

DEFAULT_SHEET = Path("data/jobs.xlsx")
DEFAULT_LEADS_SHEET = Path("data/leads.xlsx")
DEFAULT_OUTBOX = Path("outbox")
DEFAULT_PREFS = Path("preferences.yaml")

log = logging.getLogger("jobhunt")


def run_discover(prefs=DEFAULT_PREFS, sheet=DEFAULT_SHEET) -> None:
    config = load_config(prefs)
    jobs = discover(config)
    df = store.load_sheet(sheet)
    df = store.upsert(df, jobs)

    by_id = {j.id: j for j in jobs}
    for jid in df.loc[df["Status"] == "NEW", "id"]:
        job = by_id.get(str(jid))
        if job is None:
            continue
        ok, reason = score.hard_filter(job, config)
        if not ok:
            store.update_status(df, job.id, "FILTERED", FilterReason=reason)
            continue
        r = score.score_job(job, config)
        if r.score == 0:
            store.update_status(df, job.id, "FILTERED", FilterReason="score=0: no CV skills matched")
            continue
        store.update_status(
            df, job.id, "SCORED",
            Score=r.score, Matched=", ".join(r.matched),
            Missing=", ".join(r.missing),
        )

    store.save_sheet(df, sheet)
    counts = df["Status"].value_counts().to_dict()
    log.info("discover complete: %s", counts)


def run_draft(prefs=DEFAULT_PREFS, sheet=DEFAULT_SHEET, outbox=DEFAULT_OUTBOX) -> None:
    config = load_config(prefs)
    df = store.load_sheet(sheet)
    provider = MasterCVProvider(config.cv_tex_path)
    df = draft_jobs(df, config, provider, outbox)
    store.save_sheet(df, sheet)
    log.info("draft complete: %s", df["Status"].value_counts().to_dict())


def run_send(sheet=DEFAULT_SHEET, outbox=DEFAULT_OUTBOX, dry_run=False) -> None:
    df = store.load_sheet(sheet)
    if dry_run:
        sender = None
    else:
        addr, pw = load_smtp_credentials()
        sender = gmail_sender(addr, pw)
    df = send_all(df, outbox, sender=sender, dry_run=dry_run)
    store.save_sheet(df, sheet)
    log.info("send complete: %s", df["Status"].value_counts().to_dict())


def run_leads_discover(scout_name: str, keyword: str, prefs=DEFAULT_PREFS, sheet=DEFAULT_LEADS_SHEET) -> None:
    config = load_config(prefs)
    if scout_name == "academic":
        scout = AcademicScout()
        leads = scout.search(keyword)
    else:
        log.error("Unknown scout: %s", scout_name)
        return

    # Deduplicate within the new batch by name
    unique_leads = {}
    for l in leads:
        unique_leads[l.name] = l
    leads = list(unique_leads.values())

    df = leads_store.load_leads(sheet)
    df = leads_store.upsert_leads(df, leads)
    leads_store.save_leads(df, sheet)
    counts = df["Status"].value_counts().to_dict() if not df.empty else {}
    log.info("leads discover complete: %s", counts)


def run_leads_draft(prefs=DEFAULT_PREFS, sheet=DEFAULT_LEADS_SHEET) -> None:
    config = load_config(prefs)
    df = leads_store.load_leads(sheet)
    if df.empty or "Status" not in df.columns:
        log.info("No leads found.")
        return

    cv_path = Path(config.cv_tex_path)
    cv_text = cv_path.read_text(encoding="utf-8") if cv_path.exists() else ""

    leads_to_draft = df[df["Status"].isin(["NEW", "DRAFTED"])]
    for idx, row in leads_to_draft.iterrows():
        related_jobs = [j.strip() for j in str(row["RelatedJobs"]).split(",")] if pd.notna(row["RelatedJobs"]) and str(row["RelatedJobs"]).strip() else []
        lead = LeadRecord(
            id=str(row["id"]),
            name=str(row["name"]) if pd.notna(row["name"]) else "",
            org=str(row["org"]) if pd.notna(row["org"]) else "",
            title=str(row["title"]) if pd.notna(row["title"]) else "",
            discovery_source=str(row["discovery_source"]) if pd.notna(row["discovery_source"]) else "",
            context=str(row["context"]) if pd.notna(row["context"]) else "",
            user_hook=str(row["user_hook"]) if pd.notna(row["user_hook"]) else "",
            linkedin_url=str(row["linkedin_url"]) if pd.notna(row["linkedin_url"]) else None,
            social_url=str(row["social_url"]) if pd.notna(row["social_url"]) else None,
            related_jobs=related_jobs,
            status=str(row["Status"])
        )
        ice_breaker = generate_ice_breaker(lead, cv_text)
        
        df.at[idx, "user_hook"] = ice_breaker
        df.at[idx, "Status"] = "DRAFTED"
        
    leads_store.save_leads(df, sheet)
    counts = df["Status"].value_counts().to_dict() if not df.empty else {}
    log.info("leads draft complete: %s", counts)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="jobhunt", description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)
    
    sub.add_parser("discover", help="scrape, filter and score jobs")
    sub.add_parser("draft", help="prepare application emails in outbox/")
    
    s = sub.add_parser("send", help="send APPROVED applications")
    s.add_argument("--dry-run", action="store_true",
                   help="show what would be sent without sending")
                   
    leads_p = sub.add_parser("leads", help="manage networking leads")
    leads_sub = leads_p.add_subparsers(dest="leads_command", required=True)
    
    leads_discover = leads_sub.add_parser("discover", help="discover leads via scouts")
    leads_discover.add_argument("--scout", choices=["academic"], required=True, help="scout plugin to use")
    leads_discover.add_argument("--keyword", required=True, help="search keyword")
    
    leads_draft = leads_sub.add_parser("draft", help="draft ice-breakers for new leads")
    
    return p


def main(argv=None) -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    
    if args.command == "discover":
        run_discover()
    elif args.command == "draft":
        run_draft()
    elif args.command == "send":
        run_send(dry_run=args.dry_run)
    elif args.command == "leads":
        if args.leads_command == "discover":
            run_leads_discover(args.scout, args.keyword)
        elif args.leads_command == "draft":
            run_leads_draft()


if __name__ == "__main__":
    main()

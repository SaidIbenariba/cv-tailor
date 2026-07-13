# Design Spec: Unified Talent Scout System

**Date:** 2026-06-06
**Topic:** Transitioning from passive job scraping to active lead-first networking and research outreach.
**Status:** Draft

## 1. Purpose

The goal of this system is to identify high-value "Leads" (researchers, managers, and labs) in the fields of Multimodal AI, IDP, and Computer Vision. Instead of just searching for job openings, this system builds a networking database to facilitate cold outreach and relationship-building with industry and academic leaders.

## 2. Core Components

### 2.1 Lead Data Model (`LeadRecord`)

A new data structure to track people and labs, stored in `jobhunt/models.py`.

- **`id`**: Unique hash (Name + Organization).
- **`name` / `org` / `title`**: Identity and role.
- **`discovery_source`**: (ArXiv, GitHub, X/Twitter, Blog, LinkedIn).
- **`context`**: Summary of their recent work (e.g., "Author of X", "Maintainer of Y").
- **`user_hook`**: A technical bridge between the lead's work and the user's CV (e.g., specific mention of the user's PFE internship at Orange).
- **`linkedin_url` / `social_url`**: Direct links for outreach.
- **`status`**: `NEW`, `MESSAGED`, `CONNECTED`, `INTERVIEW`.
- **`related_jobs`**: Links to active job postings if they exist.

### 2.2 Discovery Scouts

A set of specialized modules (scouts) to gather leads from different platforms:

1.  **Academic Scout:** Scrapes ArXiv/Scholar for authors of papers matching keywords like "IDP" or "Qwen-VL".
2.  **Industry Scout:** Monitors engineering blogs (Mistral, Hugging Face, Orange Labs, Labs ) for technical authors.
3.  **GitHub Scout:** Identifies maintainers/contributors of trending repositories in relevant domains.
4.  **X/Twitter Scout:** Finds active researchers and hiring managers posting technical updates or hiring signals.
5.  **LinkedIn Scout:** Generates "Super-Search" URLs for safe, manual profile discovery.

### 2.3 Technical Ice-Breaker Engine

An LLM-driven module that generates highly personalized outreach messages. It combines:

- The lead's recent achievement (paper, repo, or post).
- The user's specific technical experience (IDP, air-gapped LLM deployment, medical CNNs).
- A clear call to action (connection request or resume submission).

### 2.4 Lead Database (`data/leads.xlsx`)

A separate Excel file to manage the lead lifecycle. This ensures networking activities don't clutter the main `jobs.xlsx` database.

## 3. Workflow & Data Flow

1.  **Lead Generation:** User runs `python -m jobhunt.cli leads discover --scout {academic,github,etc.}`.
2.  **Enrichment:** System populates the `user_hook` using LLM analysis of the lead's context vs the user's CV.
3.  **Job Mapping:** For every new lead, the system runs a targeted JobSpy search to see if their organization has active openings.
4.  **Outreach Preparation:** User reviews leads and runs `python -m jobhunt.cli leads draft` to generate personalized messages.
5.  **Human Action:** User uses the generated drafts and URLs to perform manual outreach on LinkedIn or via email.

## 4. Testing & Validation

- **Unit Tests:** Verify lead extraction from mock HTML/JSON responses from ArXiv and GitHub.
- **Integration Tests:** Ensure `leads.xlsx` is correctly updated and synchronized with `jobs.xlsx`.
- **Prompt Validation:** Test the Ice-Breaker Engine against various lead profiles to ensure "Technical Bridge" quality.

## 5. Future Extensions

- Automated LinkedIn connection request monitoring (where API-compliant).
- Integration with a local vector database to map user's project notes to lead's research areas.

#!/usr/bin/env python3
"""
Simple Upwork job tracker - no API needed, just paste job URLs and details.

Usage:
    python scripts/upwork_tracker.py add <job_url> --title "Job Title" --rate "$65/hr" --fit 9
    python scripts/upwork_tracker.py list
    python scripts/upwork_tracker.py update <id> --status applied
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

TRACKER_FILE = Path(__file__).parent.parent / "content" / "upwork" / "job_tracker.json"


def load_jobs() -> dict:
    """Load jobs from tracker file."""
    if TRACKER_FILE.exists():
        with open(TRACKER_FILE) as f:
            return json.load(f)
    return {"jobs": []}


def save_jobs(data: dict) -> None:
    """Save jobs to tracker file."""
    TRACKER_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKER_FILE, "w") as f:
        json.dump(data, f, indent=2)


def add_job(url: str, title: str, rate: str, fit: int, keywords: Optional[str] = None) -> None:
    """Add a new job to tracker."""
    data = load_jobs()
    job_id = len(data["jobs"]) + 1

    job = {
        "id": job_id,
        "url": url,
        "title": title,
        "rate": rate,
        "fit_score": fit,
        "keywords": keywords or "",
        "status": "starred",
        "added_date": datetime.now().isoformat(),
        "notes": ""
    }

    data["jobs"].append(job)
    save_jobs(data)
    print(f"✅ Added job #{job_id}: {title} ({rate}) - Fit: {fit}/10")


def list_jobs(status_filter: Optional[str] = None) -> None:
    """List all jobs, optionally filtered by status."""
    data = load_jobs()
    jobs = data["jobs"]

    if status_filter:
        jobs = [j for j in jobs if j["status"] == status_filter]

    if not jobs:
        print("No jobs found.")
        return

    print(f"\n{'ID':<4} {'Title':<50} {'Rate':<12} {'Fit':<4} {'Status':<12}")
    print("-" * 100)

    for job in jobs:
        print(f"{job['id']:<4} {job['title'][:48]:<50} {job['rate']:<12} {job['fit_score']:<4} {job['status']:<12}")

    print(f"\nTotal: {len(jobs)} jobs")


def update_job(job_id: int, status: Optional[str] = None, notes: Optional[str] = None) -> None:
    """Update job status or notes."""
    data = load_jobs()

    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        print(f"❌ Job #{job_id} not found")
        return

    if status:
        job["status"] = status
        job["updated_date"] = datetime.now().isoformat()

    if notes:
        job["notes"] = notes

    save_jobs(data)
    print(f"✅ Updated job #{job_id}: {job['title']}")


def show_job(job_id: int) -> None:
    """Show detailed job information."""
    data = load_jobs()

    job = next((j for j in data["jobs"] if j["id"] == job_id), None)
    if not job:
        print(f"❌ Job #{job_id} not found")
        return

    print(f"\nJob #{job['id']}: {job['title']}")
    print(f"{'='*80}")
    print(f"URL:          {job['url']}")
    print(f"Rate:         {job['rate']}")
    print(f"Fit Score:    {job['fit_score']}/10")
    print(f"Keywords:     {job['keywords']}")
    print(f"Status:       {job['status']}")
    print(f"Added:        {job['added_date']}")
    if job.get('updated_date'):
        print(f"Updated:      {job['updated_date']}")
    if job.get('notes'):
        print(f"\nNotes:\n{job['notes']}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]

    if command == "add":
        if len(sys.argv) < 4:
            print("Usage: upwork_tracker.py add <url> --title 'Job Title' --rate '$65/hr' --fit 9")
            sys.exit(1)

        url = sys.argv[2]

        # Parse arguments
        args = {}
        i = 3
        while i < len(sys.argv):
            if sys.argv[i].startswith("--"):
                key = sys.argv[i][2:]
                value = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
                args[key] = value
                i += 2
            else:
                i += 1

        add_job(
            url,
            args.get("title", "Untitled"),
            args.get("rate", "TBD"),
            int(args.get("fit", 5)),
            args.get("keywords")
        )

    elif command == "list":
        status = sys.argv[2] if len(sys.argv) > 2 else None
        list_jobs(status)

    elif command == "update":
        if len(sys.argv) < 3:
            print("Usage: upwork_tracker.py update <id> --status <status> --notes 'notes'")
            sys.exit(1)

        job_id = int(sys.argv[2])

        args = {}
        i = 3
        while i < len(sys.argv):
            if sys.argv[i].startswith("--"):
                key = sys.argv[i][2:]
                value = sys.argv[i + 1] if i + 1 < len(sys.argv) else ""
                args[key] = value
                i += 2
            else:
                i += 1

        update_job(job_id, args.get("status"), args.get("notes"))

    elif command == "show":
        if len(sys.argv) < 3:
            print("Usage: upwork_tracker.py show <id>")
            sys.exit(1)

        job_id = int(sys.argv[2])
        show_job(job_id)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

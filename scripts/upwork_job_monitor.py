#!/usr/bin/env python3
"""
Upwork Job Alert Monitor

Monitors Upwork RSS feeds for matching freelance opportunities.
Filters by keywords, scores jobs, deduplicates, and sends macOS notifications.

Setup:
    1. Install dependencies: pip install feedparser
    2. Make executable: chmod +x scripts/upwork_job_monitor.py
    3. Run manually: ./scripts/upwork_job_monitor.py
    4. Add to crontab for auto-monitoring:
       */15 * * * * cd /Users/cave/Documents/GitHub/EnterpriseHub && python3 scripts/upwork_job_monitor.py

Features:
    - Parses Upwork RSS feeds for AI/ML jobs
    - Keyword matching with positive and negative filters
    - Job scoring based on keyword match count
    - Deduplication using persistent JSON storage
    - macOS desktop notifications via osascript
    - Appends new jobs to jobs/new-jobs.md with metadata

Storage:
    - Seen job IDs: ~/.upwork_seen_jobs.json
    - New jobs log: jobs/new-jobs.md

Author: EnterpriseHub Freelance Acceleration Plan
Date: 2026-02-14
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set

try:
    import feedparser
except ImportError:
    print("ERROR: feedparser not installed. Run: pip install feedparser")
    sys.exit(1)


# Configuration
UPWORK_RSS_URLS = [
    # AI/ML category
    "https://www.upwork.com/ab/feed/jobs/rss?q=artificial+intelligence+OR+machine+learning&sort=recency",
    # Python AI
    "https://www.upwork.com/ab/feed/jobs/rss?q=python+AI+OR+chatbot+OR+RAG&sort=recency",
    # Multi-agent systems
    "https://www.upwork.com/ab/feed/jobs/rss?q=multi-agent+OR+LangChain+OR+Claude+API&sort=recency",
    # FastAPI + AI
    "https://www.upwork.com/ab/feed/jobs/rss?q=FastAPI+OR+async+python+API&sort=recency",
]

POSITIVE_KEYWORDS = [
    "rag", "llm", "claude", "gpt", "openai", "chatbot", "fastapi",
    "multi-agent", "ai automation", "python", "langchain", "vector database",
    "embeddings", "semantic search", "conversational ai", "streamlit",
    "postgresql", "redis", "async", "real-time", "enterprise",
]

NEGATIVE_KEYWORDS = [
    "wordpress", "shopify", "wix", "squarespace", "$5/hr", "$10/hr",
    "write articles", "data entry", "virtual assistant", "copy paste",
    "blog writing", "seo content", "social media posts", "logo design",
]

STORAGE_FILE = Path.home() / ".upwork_seen_jobs.json"
OUTPUT_FILE = Path(__file__).parent.parent / "jobs" / "new-jobs.md"


def load_seen_jobs() -> Set[str]:
    """Load previously seen job IDs from storage."""
    if not STORAGE_FILE.exists():
        return set()

    try:
        with open(STORAGE_FILE, 'r') as f:
            data = json.load(f)
            return set(data.get('seen_job_ids', []))
    except (json.JSONDecodeError, KeyError):
        return set()


def save_seen_jobs(seen_jobs: Set[str]) -> None:
    """Persist seen job IDs to storage."""
    with open(STORAGE_FILE, 'w') as f:
        json.dump({'seen_job_ids': list(seen_jobs)}, f, indent=2)


def extract_job_id(link: str) -> str:
    """Extract job ID from Upwork link."""
    # Upwork job links format: https://www.upwork.com/jobs/~JOBID
    if '~' in link:
        return link.split('~')[-1].split('?')[0]
    return link


def score_job(title: str, description: str) -> Dict:
    """
    Score job based on keyword matches.

    Returns:
        dict with 'score', 'matched_keywords', 'rejected' flag
    """
    content = f"{title} {description}".lower()

    # Check negative keywords first
    for neg_kw in NEGATIVE_KEYWORDS:
        if neg_kw.lower() in content:
            return {
                'score': 0,
                'matched_keywords': [],
                'rejected': True,
                'reject_reason': neg_kw
            }

    # Count positive keyword matches
    matched = []
    for pos_kw in POSITIVE_KEYWORDS:
        if pos_kw.lower() in content:
            matched.append(pos_kw)

    return {
        'score': len(matched),
        'matched_keywords': matched,
        'rejected': False,
        'reject_reason': None
    }


def extract_budget(description: str) -> str:
    """Extract budget information from job description."""
    # Common Upwork budget patterns
    budget_indicators = [
        'budget:', 'fixed price:', 'hourly rate:', '$', 'usd'
    ]

    lines = description.lower().split('\n')
    for line in lines:
        if any(indicator in line for indicator in budget_indicators):
            return line.strip()

    return "Budget not specified"


def send_notification(title: str, message: str) -> None:
    """Send macOS desktop notification."""
    script = f'''
    display notification "{message}" with title "{title}" sound name "Glass"
    '''

    try:
        subprocess.run(
            ['osascript', '-e', script],
            check=False,
            capture_output=True
        )
    except Exception as e:
        print(f"Warning: Could not send notification: {e}")


def append_to_log(job_data: Dict) -> None:
    """Append new job to jobs/new-jobs.md."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Create file with header if it doesn't exist
    if not OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, 'w') as f:
            f.write("# New Upwork Jobs\n\n")
            f.write("Auto-generated by upwork_job_monitor.py\n\n")
            f.write("---\n\n")

    # Append job entry
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    entry = f"""## {job_data['title']}

**Posted:** {timestamp}
**Score:** {job_data['score']}/10 ({len(job_data['matched_keywords'])} keyword matches)
**Budget:** {job_data['budget']}
**Link:** {job_data['link']}

**Matched Keywords:** {', '.join(job_data['matched_keywords'])}

**Description:**
```
{job_data['description'][:500]}{'...' if len(job_data['description']) > 500 else ''}
```

---

"""

    with open(OUTPUT_FILE, 'a') as f:
        f.write(entry)


def fetch_and_process_jobs() -> List[Dict]:
    """
    Fetch jobs from RSS feeds and process them.

    Returns:
        List of new job dictionaries
    """
    seen_jobs = load_seen_jobs()
    new_jobs = []

    for rss_url in UPWORK_RSS_URLS:
        try:
            feed = feedparser.parse(rss_url)

            for entry in feed.entries:
                job_id = extract_job_id(entry.link)

                # Skip if already seen
                if job_id in seen_jobs:
                    continue

                # Score the job
                title = entry.get('title', 'No title')
                description = entry.get('summary', entry.get('description', ''))

                score_result = score_job(title, description)

                # Skip rejected jobs
                if score_result['rejected']:
                    print(f"REJECTED: {title} (reason: {score_result['reject_reason']})")
                    seen_jobs.add(job_id)
                    continue

                # Skip low-score jobs (< 2 keyword matches)
                if score_result['score'] < 2:
                    print(f"LOW SCORE: {title} (score: {score_result['score']})")
                    seen_jobs.add(job_id)
                    continue

                # Extract budget
                budget = extract_budget(description)

                job_data = {
                    'job_id': job_id,
                    'title': title,
                    'link': entry.link,
                    'description': description,
                    'score': score_result['score'],
                    'matched_keywords': score_result['matched_keywords'],
                    'budget': budget,
                    'published': entry.get('published', 'Unknown'),
                }

                new_jobs.append(job_data)
                seen_jobs.add(job_id)

                print(f"NEW JOB: {title} (score: {score_result['score']})")

        except Exception as e:
            print(f"ERROR fetching feed {rss_url}: {e}")
            continue

    # Save updated seen jobs
    save_seen_jobs(seen_jobs)

    return new_jobs


def main():
    """Main execution."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Upwork Job Monitor started")
    print(f"Monitoring {len(UPWORK_RSS_URLS)} RSS feeds...")

    new_jobs = fetch_and_process_jobs()

    if not new_jobs:
        print("No new jobs found matching criteria.")
        return

    print(f"\nFound {len(new_jobs)} new matching jobs!")

    # Sort by score (highest first)
    new_jobs.sort(key=lambda x: x['score'], reverse=True)

    # Log all new jobs
    for job in new_jobs:
        append_to_log(job)

    # Send notification for top job
    top_job = new_jobs[0]
    send_notification(
        "New Upwork Job Match!",
        f"{top_job['title']} (Score: {top_job['score']})"
    )

    print(f"\n✓ Logged {len(new_jobs)} jobs to {OUTPUT_FILE}")
    print(f"✓ Desktop notification sent for top job")
    print(f"\nTop job: {top_job['title']} (score: {top_job['score']})")
    print(f"Link: {top_job['link']}")


if __name__ == '__main__':
    main()

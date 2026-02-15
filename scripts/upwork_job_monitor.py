#!/usr/bin/env python3
"""
Upwork Job Alert Monitor

Monitors Upwork RSS feeds for matching freelance opportunities.
Filters by weighted keyword scoring, deduplicates, and sends Slack + macOS alerts.

Setup:
    1. Install dependencies: pip install feedparser requests
    2. Set env var: export UPWORK_SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
    3. Make executable: chmod +x scripts/upwork_job_monitor.py
    4. Run manually: ./scripts/upwork_job_monitor.py
    5. Add to crontab for auto-monitoring:
       */15 * * * * cd /Users/cave/Documents/GitHub/EnterpriseHub && python3 scripts/upwork_job_monitor.py >> jobs/monitor.log 2>&1

Features:
    - Parses Upwork RSS feeds for AI/ML jobs
    - Weighted keyword scoring (0-10 scale) with premium/solid/quickwin tiers
    - Slack Block Kit notifications with color-coded scores
    - macOS desktop notifications as backup
    - Deduplication using persistent JSON storage
    - Appends new jobs to jobs/new-jobs.md with metadata
    - Priority classification: P1 (8+), P2 (5-7), Skip (<5)

Storage:
    - Seen job IDs: ~/.upwork_seen_jobs.json
    - New jobs log: jobs/new-jobs.md
"""

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import feedparser
except ImportError:
    print("ERROR: feedparser not installed. Run: pip install feedparser")
    sys.exit(1)

try:
    import requests
except ImportError:
    requests = None  # Slack alerts disabled, macOS notifications still work


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

UPWORK_RSS_URLS = [
    # AI/ML category
    "https://www.upwork.com/ab/feed/jobs/rss?q=artificial+intelligence+OR+machine+learning&sort=recency",
    # Python AI
    "https://www.upwork.com/ab/feed/jobs/rss?q=python+AI+OR+chatbot+OR+RAG&sort=recency",
    # Multi-agent systems
    "https://www.upwork.com/ab/feed/jobs/rss?q=multi-agent+OR+LangChain+OR+Claude+API&sort=recency",
    # FastAPI + AI
    "https://www.upwork.com/ab/feed/jobs/rss?q=FastAPI+OR+async+python+API&sort=recency",
    # Streamlit + dashboards
    "https://www.upwork.com/ab/feed/jobs/rss?q=streamlit+OR+data+dashboard+python&sort=recency",
]

# Weighted keyword tiers — weights contribute to a normalized 0-10 score.
# Premium ($70+/hr potential), Solid ($60-75/hr), Quick Win ($500+ fixed)
KEYWORD_TIERS: Dict[str, List[Tuple[str, float]]] = {
    "premium": [
        ("claude api", 10),
        ("multi-agent", 10),
        ("rag optimization", 9),
        ("llm cost reduction", 9),
        ("ai orchestration", 9),
        ("agent framework", 9),
        ("langchain agent", 8),
        ("crewai", 8),
        ("autogen", 8),
        ("rag pipeline", 8),
    ],
    "solid": [
        ("rag", 7),
        ("fastapi", 7),
        ("vector database", 7),
        ("streamlit", 6),
        ("embeddings", 6),
        ("semantic search", 6),
        ("chatbot", 6),
        ("conversational ai", 6),
        ("claude", 5),
        ("openai", 5),
        ("llm", 5),
        ("langchain", 5),
        ("gpt", 5),
        ("pinecone", 5),
        ("weaviate", 5),
        ("chromadb", 5),
    ],
    "quickwin": [
        ("proof of concept", 4),
        ("python automation", 4),
        ("python script", 3),
        ("api integration", 3),
        ("postgresql", 3),
        ("redis", 3),
        ("async", 3),
        ("real-time", 3),
        ("enterprise", 3),
        ("data pipeline", 3),
    ],
}

NEGATIVE_KEYWORDS = [
    "wordpress", "shopify", "wix", "squarespace", "$5/hr", "$10/hr",
    "write articles", "data entry", "virtual assistant", "copy paste",
    "blog writing", "seo content", "social media posts", "logo design",
    "php developer", "ruby on rails", "ionic", "flutter",
]

SLACK_WEBHOOK_URL = os.getenv("UPWORK_SLACK_WEBHOOK_URL", "")
STORAGE_FILE = Path.home() / ".upwork_seen_jobs.json"
OUTPUT_FILE = Path(__file__).parent.parent / "jobs" / "new-jobs.md"

# Score thresholds
P1_THRESHOLD = 8.0  # Immediate alert
P2_THRESHOLD = 5.0  # Batched / lower priority
MIN_SCORE = 3.0     # Below this = skip entirely


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_seen_jobs() -> Set[str]:
    """Load previously seen job IDs from storage."""
    if not STORAGE_FILE.exists():
        return set()
    try:
        with open(STORAGE_FILE, "r") as f:
            data = json.load(f)
            return set(data.get("seen_job_ids", []))
    except (json.JSONDecodeError, KeyError):
        return set()


def save_seen_jobs(seen_jobs: Set[str]) -> None:
    """Persist seen job IDs to storage."""
    with open(STORAGE_FILE, "w") as f:
        json.dump({"seen_job_ids": list(seen_jobs)}, f, indent=2)


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def extract_job_id(link: str) -> str:
    """Extract job ID from Upwork link."""
    if "~" in link:
        return link.split("~")[-1].split("?")[0]
    return link


def score_job(title: str, description: str) -> Dict:
    """
    Score a job using weighted keyword matching on a 0-10 scale.

    The score is: (sum of matched keyword weights) / (max possible single-tier weight) * 10,
    capped at 10. This means a single premium keyword match (weight 10) gives a score of 10,
    while a single quickwin match (weight 3) gives 3.0.
    """
    content = f"{title} {description}".lower()

    # Check negative keywords first
    for neg_kw in NEGATIVE_KEYWORDS:
        if neg_kw.lower() in content:
            return {
                "score": 0.0,
                "matched_keywords": [],
                "matched_tiers": {},
                "rejected": True,
                "reject_reason": neg_kw,
                "priority": "Skip",
            }

    # Weighted keyword matching — deduplicate (a keyword only scores once)
    matched_keywords = []
    matched_tiers: Dict[str, List[str]] = {"premium": [], "solid": [], "quickwin": []}
    total_weight = 0.0
    seen_keywords: Set[str] = set()

    for tier_name, keywords in KEYWORD_TIERS.items():
        for keyword, weight in keywords:
            kw_lower = keyword.lower()
            if kw_lower not in seen_keywords and kw_lower in content:
                seen_keywords.add(kw_lower)
                matched_keywords.append(keyword)
                matched_tiers[tier_name].append(keyword)
                total_weight += weight

    # Normalize to 0-10: use top weight (10) as reference ceiling
    score = min(total_weight / 10.0 * 10.0, 10.0)
    # Simpler: score = min(total_weight, 10.0) since max single weight is 10
    score = min(total_weight, 10.0)

    # Classify priority
    if score >= P1_THRESHOLD:
        priority = "P1"
    elif score >= P2_THRESHOLD:
        priority = "P2"
    else:
        priority = "Skip"

    return {
        "score": round(score, 1),
        "matched_keywords": matched_keywords,
        "matched_tiers": matched_tiers,
        "rejected": False,
        "reject_reason": None,
        "priority": priority,
    }


def extract_budget(description: str) -> str:
    """Extract budget information from job description."""
    # Try structured budget patterns first
    hourly = re.search(r"\$(\d+(?:\.\d+)?)\s*[-–]\s*\$?(\d+(?:\.\d+)?)\s*/?\s*h(?:ou)?r", description, re.I)
    if hourly:
        return f"${hourly.group(1)}-${hourly.group(2)}/hr"

    fixed = re.search(r"(?:budget|fixed.?price)[:\s]*\$?([\d,]+)", description, re.I)
    if fixed:
        return f"${fixed.group(1)} fixed"

    # Fallback: any dollar amount
    dollar = re.search(r"\$([\d,]+(?:\.\d+)?)", description)
    if dollar:
        return f"${dollar.group(1)}"

    return "Budget not specified"


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def _score_color(score: float) -> str:
    """Return Slack color hex for score."""
    if score >= P1_THRESHOLD:
        return "#2eb886"  # green
    if score >= P2_THRESHOLD:
        return "#daa038"  # orange
    return "#a0a0a0"      # gray


def send_slack_alert(jobs: List[Dict]) -> bool:
    """
    Send Slack Block Kit notification for new jobs.

    Groups jobs by priority. P1 gets individual rich cards, P2 gets a summary list.
    Returns True if sent successfully, False otherwise.
    """
    if not SLACK_WEBHOOK_URL or requests is None:
        return False

    p1_jobs = [j for j in jobs if j["priority"] == "P1"]
    p2_jobs = [j for j in jobs if j["priority"] == "P2"]

    attachments = []

    # P1 jobs: individual rich cards
    for job in p1_jobs:
        tier_text = ""
        for tier, kws in job["matched_tiers"].items():
            if kws:
                tier_text += f"*{tier.title()}*: {', '.join(kws)}\n"

        attachments.append({
            "color": _score_color(job["score"]),
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": (
                            f"*:fire: P1 — {job['title']}*\n"
                            f"Score: *{job['score']}/10* | Budget: {job['budget']}\n"
                            f"{tier_text}"
                        ),
                    },
                    "accessory": {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Job"},
                        "url": job["link"],
                        "action_id": f"view_job_{job['job_id'][:8]}",
                    },
                },
            ],
        })

    # P2 jobs: compact summary
    if p2_jobs:
        lines = []
        for job in p2_jobs[:10]:  # cap at 10
            lines.append(
                f"- <{job['link']}|{job['title']}> (score: {job['score']}, {job['budget']})"
            )
        attachments.append({
            "color": _score_color(5.0),
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*P2 Jobs ({len(p2_jobs)})*\n" + "\n".join(lines),
                    },
                },
            ],
        })

    if not attachments:
        return False

    payload = {
        "text": f"Upwork Monitor: {len(p1_jobs)} P1, {len(p2_jobs)} P2 new jobs",
        "attachments": attachments,
    }

    try:
        resp = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"Slack alert sent: {len(p1_jobs)} P1, {len(p2_jobs)} P2")
            return True
        print(f"Slack error: {resp.status_code} {resp.text[:200]}")
        return False
    except Exception as e:
        print(f"Slack send failed: {e}")
        return False


def send_notification(title: str, message: str) -> None:
    """Send macOS desktop notification."""
    # Escape quotes for osascript
    safe_msg = message.replace('"', '\\"')[:200]
    safe_title = title.replace('"', '\\"')[:100]
    script = f'display notification "{safe_msg}" with title "{safe_title}" sound name "Glass"'
    try:
        subprocess.run(["osascript", "-e", script], check=False, capture_output=True)
    except Exception as e:
        print(f"Warning: Could not send notification: {e}")


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def append_to_log(job_data: Dict) -> None:
    """Append new job to jobs/new-jobs.md."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not OUTPUT_FILE.exists():
        with open(OUTPUT_FILE, "w") as f:
            f.write("# New Upwork Jobs\n\nAuto-generated by upwork_job_monitor.py\n\n---\n\n")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tier_info = ""
    for tier, kws in job_data.get("matched_tiers", {}).items():
        if kws:
            tier_info += f"  - {tier.title()}: {', '.join(kws)}\n"

    entry = f"""## [{job_data['priority']}] {job_data['title']}

**Posted:** {timestamp}
**Score:** {job_data['score']}/10 ({job_data['priority']})
**Budget:** {job_data['budget']}
**Link:** {job_data['link']}

**Matched Keywords:**
{tier_info}
**Description:**
```
{job_data['description'][:500]}{'...' if len(job_data['description']) > 500 else ''}
```

---

"""
    with open(OUTPUT_FILE, "a") as f:
        f.write(entry)


# ---------------------------------------------------------------------------
# Core pipeline
# ---------------------------------------------------------------------------

def fetch_and_process_jobs() -> List[Dict]:
    """Fetch jobs from RSS feeds, score, deduplicate, and return new matches."""
    seen_jobs = load_seen_jobs()
    new_jobs: List[Dict] = []

    for rss_url in UPWORK_RSS_URLS:
        try:
            feed = feedparser.parse(rss_url)
            for entry in feed.entries:
                job_id = extract_job_id(entry.link)
                if job_id in seen_jobs:
                    continue

                title = entry.get("title", "No title")
                description = entry.get("summary", entry.get("description", ""))
                score_result = score_job(title, description)

                seen_jobs.add(job_id)

                if score_result["rejected"]:
                    print(f"  REJECTED: {title} ({score_result['reject_reason']})")
                    continue

                if score_result["score"] < MIN_SCORE:
                    print(f"  LOW: {title} (score: {score_result['score']})")
                    continue

                budget = extract_budget(description)

                job_data = {
                    "job_id": job_id,
                    "title": title,
                    "link": entry.link,
                    "description": description,
                    "score": score_result["score"],
                    "matched_keywords": score_result["matched_keywords"],
                    "matched_tiers": score_result["matched_tiers"],
                    "budget": budget,
                    "priority": score_result["priority"],
                    "published": entry.get("published", "Unknown"),
                }
                new_jobs.append(job_data)
                print(f"  NEW [{score_result['priority']}]: {title} (score: {score_result['score']})")

        except Exception as e:
            print(f"  ERROR fetching {rss_url[:60]}...: {e}")

    save_seen_jobs(seen_jobs)
    return new_jobs


def main():
    """Main execution — fetch, score, notify."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Upwork Job Monitor")
    print(f"  Feeds: {len(UPWORK_RSS_URLS)} | Slack: {'ON' if SLACK_WEBHOOK_URL else 'OFF'}")

    new_jobs = fetch_and_process_jobs()

    if not new_jobs:
        print("  No new jobs matching criteria.")
        return

    # Sort by score descending
    new_jobs.sort(key=lambda x: x["score"], reverse=True)

    # Log all to markdown
    for job in new_jobs:
        append_to_log(job)

    # Slack alert (P1 + P2 combined)
    alertable = [j for j in new_jobs if j["priority"] in ("P1", "P2")]
    if alertable:
        send_slack_alert(alertable)

    # macOS notification for top job
    top = new_jobs[0]
    send_notification(
        f"Upwork {top['priority']}: Score {top['score']}/10",
        top["title"][:100],
    )

    p1_count = sum(1 for j in new_jobs if j["priority"] == "P1")
    p2_count = sum(1 for j in new_jobs if j["priority"] == "P2")
    print(f"\n  Found {len(new_jobs)} jobs: {p1_count} P1, {p2_count} P2")
    print(f"  Top: {top['title']} (score: {top['score']}, {top['priority']})")
    print(f"  Logged to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()

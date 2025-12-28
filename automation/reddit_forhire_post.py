#!/usr/bin/env python3
"""
Reddit r/forhire Auto-Poster
Posts your services to r/forhire automatically.

Setup:
1. Create Reddit app: https://www.reddit.com/prefs/apps
2. Copy client_id, client_secret, username, password
3. Install: pip install praw
4. Run: python reddit_forhire_post.py
"""

import praw
from datetime import datetime

# CONFIGURATION - Replace with your values
REDDIT_CONFIG = {
    "client_id": "YOUR_CLIENT_ID",  # From https://www.reddit.com/prefs/apps
    "client_secret": "YOUR_CLIENT_SECRET",
    "username": "YOUR_REDDIT_USERNAME",
    "password": "YOUR_REDDIT_PASSWORD",
    "user_agent": "ForHirePoster/1.0",
}

# Your service post template
POST_TITLE = "[FOR HIRE] Python/Streamlit Developer - $50/hr - Enterprise Dashboards & AI Integration"

POST_BODY = """**About Me:**
IBM-Certified AI Engineer & Google-Certified BI Professional with 1,700+ hours of specialized training.

**What I Build:**
- Interactive Streamlit dashboards (financial analysis, data visualization)
- AI automation (Claude 3.5, GPT-4 integration)
- Web scraping & data pipelines (BeautifulSoup, Selenium, pandas)
- API integrations & backend systems

**Proof of Work:**
https://github.com/ChunkyTortoise/EnterpriseHub
- 311+ automated tests (100% pass rate)
- 7 production-grade modules
- Real-time market analysis, sentiment tracking, cost-volume-profit modeling

**Recent Projects:**
- Built multi-module BI platform with 311 tests
- Integrated Claude 3.5 API for AI content generation
- Created 10x10 sensitivity heatmap for financial modeling
- Deployed production Streamlit apps on cloud

**Rates:**
- Hourly: $50-75/hr (depending on complexity)
- Fixed-price: Starting at $300 for small projects

**Tech Stack:**
Python, Streamlit, Plotly, pandas, NumPy, Anthropic API, OpenAI API, yfinance, BeautifulSoup, Selenium, pytest, GitHub Actions

**Availability:** 20-30 hours/week

**Contact:**
- GitHub: https://github.com/ChunkyTortoise/EnterpriseHub
- DM me here or reply to this post

**Looking for:**
- Dashboard development projects
- AI automation/integration work
- Data pipeline & scraping projects
- Long-term contracts (3-6 months+)

Happy to provide references and discuss your project requirements!
"""


def post_to_reddit():
    """Post to r/forhire"""
    try:
        # Initialize Reddit instance
        reddit = praw.Reddit(**REDDIT_CONFIG)

        # Post to r/forhire
        subreddit = reddit.subreddit("forhire")
        submission = subreddit.submit(POST_TITLE, selftext=POST_BODY)

        print(f"✅ Posted successfully!")
        print(f"📍 URL: {submission.url}")
        print(f"🕐 Posted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return submission.url

    except Exception as e:
        print(f"❌ Error posting to Reddit: {e}")
        return None


def main():
    """Main entry point"""
    print("🚀 Reddit r/forhire Auto-Poster")
    print("=" * 50)

    # Validate config
    if REDDIT_CONFIG["client_id"] == "YOUR_CLIENT_ID":
        print("❌ ERROR: You need to configure your Reddit API credentials first!")
        print("\nSteps:")
        print("1. Go to https://www.reddit.com/prefs/apps")
        print("2. Click 'Create App' or 'Create Another App'")
        print("3. Fill in:")
        print("   - Name: ForHirePoster")
        print("   - Type: Script")
        print("   - Redirect URI: http://localhost:8080")
        print("4. Copy 'client_id' and 'client_secret' into this script")
        print("5. Add your Reddit username and password")
        return

    # Post
    url = post_to_reddit()

    if url:
        print("\n✅ SUCCESS! Your post is live.")
        print(f"\n📋 Next steps:")
        print("1. Monitor responses in your Reddit inbox")
        print("2. Reply to interested clients within 2 hours")
        print("3. Repost every 7 days (r/forhire rules)")


if __name__ == "__main__":
    main()

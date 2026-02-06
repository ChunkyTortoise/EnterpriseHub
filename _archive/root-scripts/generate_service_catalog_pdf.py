#!/usr/bin/env python3
"""
Generate a professional PDF from the Service Catalog markdown.
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor, black, white
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    KeepTogether,
)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import re


# Professional color scheme
PRIMARY_COLOR = HexColor("#1a1a2e")  # Dark navy
ACCENT_COLOR = HexColor("#16213e")  # Darker navy
HIGHLIGHT_COLOR = HexColor("#0f3460")  # Medium blue
TEXT_COLOR = HexColor("#2d2d44")  # Dark gray
LIGHT_BG = HexColor("#f8f9fa")  # Light gray background


class ServiceCatalogPDF:
    def __init__(self, filename="Service_Catalog.pdf"):
        self.filename = filename
        self.doc = SimpleDocTemplate(
            filename,
            pagesize=letter,
            rightMargin=0.75 * inch,
            leftMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        self.story = []
        self.setup_styles()

    def setup_styles(self):
        """Create professional paragraph styles."""
        styles = getSampleStyleSheet()

        # Title style
        self.title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=28,
            textColor=PRIMARY_COLOR,
            spaceAfter=12,
            spaceBefore=24,
            alignment=TA_CENTER,
            fontName="Helvetica-Bold",
        )

        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Normal"],
            fontSize=11,
            textColor=TEXT_COLOR,
            spaceAfter=18,
            alignment=TA_CENTER,
            fontName="Helvetica",
        )

        # Heading 1 style
        self.h1_style = ParagraphStyle(
            "CustomH1",
            parent=styles["Heading1"],
            fontSize=20,
            textColor=PRIMARY_COLOR,
            spaceAfter=12,
            spaceBefore=24,
            fontName="Helvetica-Bold",
            borderWidth=0,
            borderPadding=0,
            backColor=LIGHT_BG,
            leftIndent=0,
        )

        # Heading 2 style
        self.h2_style = ParagraphStyle(
            "CustomH2",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=HIGHLIGHT_COLOR,
            spaceAfter=10,
            spaceBefore=18,
            fontName="Helvetica-Bold",
        )

        # Heading 3 style
        self.h3_style = ParagraphStyle(
            "CustomH3",
            parent=styles["Heading3"],
            fontSize=14,
            textColor=HIGHLIGHT_COLOR,
            spaceAfter=8,
            spaceBefore=14,
            fontName="Helvetica-Bold",
        )

        # Body text style
        self.body_style = ParagraphStyle(
            "CustomBody",
            parent=styles["Normal"],
            fontSize=10,
            textColor=TEXT_COLOR,
            spaceAfter=8,
            alignment=TA_JUSTIFY,
            fontName="Helvetica",
            leading=14,
        )

        # Bold body style
        self.bold_style = ParagraphStyle(
            "CustomBold",
            parent=self.body_style,
            fontName="Helvetica-Bold",
        )

        # Bullet style
        self.bullet_style = ParagraphStyle(
            "CustomBullet",
            parent=self.body_style,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=6,
        )

    def add_header(self, canvas_obj, doc):
        """Add header to each page."""
        canvas_obj.saveState()
        canvas_obj.setFillColor(PRIMARY_COLOR)
        canvas_obj.rect(0, letter[1] - 0.5 * inch, letter[0], 0.5 * inch, fill=1)
        canvas_obj.setFillColor(white)
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawCentredString(
            letter[0] / 2.0, letter[1] - 0.35 * inch, "Service Catalog"
        )
        canvas_obj.restoreState()

    def add_footer(self, canvas_obj, doc):
        """Add footer with page numbers."""
        canvas_obj.saveState()
        canvas_obj.setFont("Helvetica", 9)
        canvas_obj.setFillColor(TEXT_COLOR)
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"
        canvas_obj.drawCentredString(letter[0] / 2.0, 0.5 * inch, text)
        canvas_obj.restoreState()

    def parse_markdown(self, content):
        """Parse markdown content and convert to PDF elements."""
        lines = content.split("\n")
        i = 0

        while i < len(lines):
            line = lines[i].strip()

            if not line:
                self.story.append(Spacer(1, 6))
                i += 1
                continue

            # Title (first line)
            if i == 0 and line.startswith("# "):
                title = line[2:].strip()
                self.story.append(Paragraph(title, self.title_style))
                i += 1
                continue

            # H1 headings
            if line.startswith("# "):
                text = line[2:].strip()
                self.story.append(Spacer(1, 12))
                self.story.append(Paragraph(text, self.h1_style))
                i += 1
                continue

            # H2 headings
            if line.startswith("## "):
                text = line[3:].strip()
                self.story.append(Spacer(1, 10))
                self.story.append(Paragraph(text, self.h2_style))
                i += 1
                continue

            # H3 headings
            if line.startswith("### "):
                text = line[4:].strip()
                self.story.append(Spacer(1, 8))
                self.story.append(Paragraph(text, self.h3_style))
                i += 1
                continue

            # Horizontal rule
            if line.startswith("---"):
                self.story.append(Spacer(1, 12))
                i += 1
                continue

            # Bold text (handled in paragraph processing)
            # Bullet points
            if line.startswith("- ") or line.startswith("* "):
                bullet_text = line[2:].strip()
                # Process inline formatting
                bullet_text = self.process_inline_formatting(bullet_text)
                self.story.append(Paragraph(f"• {bullet_text}", self.bullet_style))
                i += 1
                continue

            # Regular paragraph
            if line:
                # Process inline formatting (bold, etc.)
                formatted_text = self.process_inline_formatting(line)
                self.story.append(Paragraph(formatted_text, self.body_style))
                i += 1
                continue

            i += 1

    def process_inline_formatting(self, text):
        """Process markdown inline formatting to ReportLab format."""
        # Bold text **text** or **text**
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        # Italic *text*
        text = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", text)
        # Escape HTML special characters
        text = text.replace("&", "&amp;")
        return text

    def build_pdf(self, content):
        """Build the complete PDF."""
        self.parse_markdown(content)

        # Build PDF with custom header/footer
        self.doc.build(
            self.story,
            onFirstPage=self.add_header,
            onLaterPages=self.add_header,
            canvasmaker=lambda *args, **kwargs: self._add_footer_canvas(*args, **kwargs),
        )

    def _add_footer_canvas(self, *args, **kwargs):
        """Create canvas with footer."""
        canvas_obj = canvas.Canvas(*args, **kwargs)
        original_showPage = canvas_obj.showPage

        def new_showPage():
            self.add_footer(canvas_obj, self.doc)
            original_showPage()

        canvas_obj.showPage = new_showPage
        return canvas_obj


def main():
    """Main function to generate PDF."""
    markdown_content = """# Service Catalog: AI, Data Science & Business Intelligence

**Prepared by:** Cayman Roden | Senior AI Engineer & Data Strategist  
**Availability:** Limited to 2-3 projects per quarter | Accepting Q1 2026 engagements

---

## Executive Summary

I build **production-grade AI systems and data infrastructure** for serious businesses. Unlike typical freelancers, every project includes:

- **300+ automated tests** covering critical functionality (no surprises post-launch)
- **Enterprise architecture** — code that scales as your business grows
- **Zero tech debt** — properly documented, maintainable, production-ready
- **Direct impact on revenue** — I optimize for business outcomes, not feature count

**No offshore dev shops. No junior coders. No "good enough" solutions.**

My background spans **Vanderbilt GenAI, IBM GenAI Engineering, Duke LLMOps, Google Advanced Data Analytics, and Microsoft certifications** — but more importantly, I've delivered systems that directly impacted client revenue and operational efficiency.

---

## Service Overview

I specialize in three core areas: **AI Automation**, **Data Intelligence**, and **Legacy Modernization**.

---

## 1. AI & Intelligent Automation Agents

*Certified through: Vanderbilt GenAI, IBM GenAI Engineering, Duke LLMOps*

### A. Custom RAG Conversational Agents (The "Production AI Assistant")

Intelligent agents that read your proprietary documents, knowledge bases, and databases to answer client questions in real-time. Not a simple chatbot — a **system that understands context, cites sources, and reduces support load by 60%+**.

**Who needs this:**
- Real estate teams managing 100+ property inquiries/month
- SaaS companies fielding repetitive customer support questions
- Law firms automating contract Q&A
- Insurance brokers handling policy questions at scale

**What you get:**
- Python backend using LangChain/LangGraph with production error handling
- Vector database setup (Pinecone/Chroma) with semantic search optimization
- Webhook integration with your CRM (GHL, Zapier, HubSpot, Salesforce)
- Automated testing suite with >95% code coverage
- Full Git repository + deployment documentation
- 30-day free maintenance & bug fixes included

**Timeline:** 3–5 business days  
**Investment:** **$3,500 - $5,000**

---

### B. Multi-Agent Workflows (The "Autonomous Team")

Orchestrate multiple specialized AI agents working together on complex tasks. Example: Agent 1 scrapes leads → Agent 2 research company background on LinkedIn → Agent 3 personalizes outreach email → Agent 4 schedules follow-up.

**Who needs this:**
- Agencies managing outbound prospecting at scale
- E-commerce businesses automating competitive research
- Recruitment firms automating candidate screening workflows
- B2B companies automating lead enrichment pipelines

**What you get:**
- Multi-agent system using CrewAI or AutoGen framework
- Error handling, retry logic, and failed-task notifications
- Output reports with full audit trail of agent decisions
- Integration with your business tools (Slack, email, CRM)
- Automated testing + monitoring dashboard
- 30-day free maintenance included

**Timeline:** 5–7 business days  
**Investment:** **$5,000 - $8,000**

---

### C. Prompt Engineering & System Optimization

Deep audit and optimization of your existing AI implementations. Reduce hallucinations, improve response quality, increase conversion rates.

**Who needs this:**
- Teams with existing bots performing suboptimally (<70% accuracy)
- Companies looking to improve LLM consistency across workflows
- Organizations wanting to switch from GPT-4 to more cost-effective models
- Teams requiring custom system instructions for brand-specific responses

**What you get:**
- Comprehensive audit of current prompts and performance metrics
- A/B tested prompt libraries with performance comparisons
- System instructions documentation tailored to your use case
- Cost optimization analysis (potential 40% savings)
- Implementation guide with before/after metrics

**Timeline:** 1–2 business days  
**Investment:** **$1,200 - $1,800**

---

## 2. Business Intelligence & Data Infrastructure

*Certified through: Google Data Analytics, IBM BI Analyst, Microsoft Power BI*

### D. Interactive Business Intelligence Dashboards

Custom data visualization platform connecting to your live data sources. Not a template — a purpose-built dashboard optimized for YOUR business metrics.

**Who needs this:**
- SaaS companies tracking CAC, LTV, churn, and unit economics
- E-commerce businesses monitoring conversion funnels and inventory
- Agencies displaying client campaign performance in real-time
- Manufacturing companies tracking KPIs across operations
- Financial services tracking risk metrics and portfolio performance

**What you get:**
- Streamlit or Power BI dashboard (your choice)
- Live data connections (Google Sheets, SQL databases, REST APIs, Salesforce, HubSpot)
- Interactive filters, drill-downs, and custom calculations
- Automated daily/weekly reporting to stakeholders
- Mobile-responsive design
- User authentication and role-based access controls
- 30 days of free updates and adjustments

**Timeline:** 3–5 business days  
**Investment:** **$3,000 - $5,000**

---

### E. Automated Reporting Pipelines

Stop manually aggregating data into Excel each week. I build pipelines that **automatically clean, transform, and email polished reports** to your stakeholders.

**Who needs this:**
- Sales teams sending weekly pipeline reports
- Marketing teams tracking ad spend and attribution
- Finance teams producing monthly P&L summaries
- Operations teams monitoring KPIs across locations
- Executive teams receiving board-ready dashboards

**What you get:**
- Fully automated Python pipeline (no human intervention needed)
- Scheduled execution (daily, weekly, monthly — your choice)
- Email delivery with formatted reports, charts, and summaries
- Error notifications if data sources fail
- Version control and audit logging
- Maintenance and support included (first 30 days free)

**Timeline:** 2–3 business days  
**Investment:** **$2,000 - $3,000**

---

### F. Predictive Analytics & Lead Scoring

Use machine learning to predict **which leads will actually close**, which customers will churn, or which products will sell best.

**Who needs this:**
- Real estate teams prioritizing leads by close probability
- SaaS companies identifying at-risk customer accounts
- E-commerce businesses optimizing marketing spend by predicted LTV
- B2B sales teams focusing on high-probability opportunities
- Insurance companies assessing risk profiles

**What you get:**
- Data audit and feature engineering
- Trained ML model (Scikit-Learn/XGBoost/LightGBM)
- Accuracy metrics + model explainability (why each prediction)
- Prediction API or automated scoring system
- Integration with your CRM (automated field updates)
- 30-day free model tuning and improvements

**Timeline:** 5–7 business days  
**Investment:** **$4,000 - $6,000**

---

## 3. Marketing Tech & Content Automation

*Certified through: Meta Social Media Marketing, Google Digital Marketing*

### G. Programmatic SEO Content Engines

Build systems that **automatically research, write, and publish SEO-optimized content** at scale. Not generic ChatGPT output — proper articles with research, citations, and brand voice.

**Who needs this:**
- SaaS companies scaling blog content across 50+ landing pages
- E-commerce businesses creating product comparison guides
- Local service businesses targeting hundreds of geographic markets
- News/content sites producing daily coverage at scale
- Real estate agents creating neighborhood guides

**What you get:**
- Python system that researches topics using live APIs
- Generates SEO-optimized articles in your brand voice
- Automatic keyword integration and meta tag generation
- Bulk publishing to WordPress or direct file export
- Performance tracking (impressions, CTR, conversion by article)
- Content calendar and editing interface

**Timeline:** 3–5 business days  
**Investment:** **$4,000 - $6,500**

---

### H. Social Sentiment & Brand Monitoring

Real-time monitoring of what customers, competitors, and the market are saying about you across Reddit, Twitter, news sites, and review platforms.

**Who needs this:**
- Brands launching new products (need rapid feedback loops)
- Companies managing PR/crisis situations
- Competitors tracking sentiment vs. competitors
- Startups monitoring market reception
- E-commerce businesses watching review sites

**What you get:**
- Automated scraping and sentiment analysis across platforms
- Real-time dashboard with alert thresholds
- Sentiment scoring (Positive/Negative/Neutral/Mixed)
- Trending topics and keyword analysis
- Weekly digest reports
- Alert system (Slack notifications for spikes)

**Timeline:** 3–4 business days  
**Investment:** **$3,000 - $4,500**

---

### I. Marketing Attribution & ROI Analysis

Stop guessing which channels drive revenue. I conduct deep-dive analysis: **Which ad spend actually generates customers? What's your true CAC by channel? Which campaigns move the needle?**

**Who needs this:**
- E-commerce businesses with multi-channel ad spend
- SaaS companies trying to optimize marketing budget allocation
- Agencies justifying ad spend to clients
- Founders making go/no-go decisions on marketing channels
- Brands with complex customer journeys

**What you get:**
- Complete marketing data audit (Google Ads, Facebook, email, organic, etc.)
- Customer journey analysis and attribution modeling
- CAC by channel + LTV analysis
- ROI projections and optimization recommendations
- Interactive dashboard + comprehensive written report
- Presented insights ready for board meetings

**Timeline:** 3–4 business days  
**Investment:** **$2,500 - $4,000**

---

## 4. Legacy System Modernization

*Certified through: Python for Everybody, Google Cloud Architecture*

### J. "Excel to Web App" Modernization

Transform your slow, fragile, multi-user Excel sheets into **fast, scalable, secure web applications** your team actually enjoys using.

**Who needs this:**
- Finance teams managing complex spreadsheet workflows
- Operations managing inventory, scheduling, or resource allocation
- Sales teams with shared forecasting models
- Any team where "the Excel file is too slow" or "everyone keeps breaking it"

**What you get:**
- Modern web application (Streamlit, FastAPI, or React based on complexity)
- Secure database (PostgreSQL or SQLite, your choice)
- User authentication and role-based permissions
- Data migration from existing Excel
- Training for your team (1-hour video walkthrough)
- 30 days free support and adjustments
- Full source code + deployment documentation

**Timeline:** 4–7 business days  
**Investment:** **$6,000 - $12,000**

---

### K. Competitor Intelligence & Web Scraping

Automated bots that monitor competitor pricing, product changes, or availability in real-time.

**Who needs this:**
- E-commerce businesses optimizing pricing against competitors
- Real estate teams tracking competitive listings and prices
- Airlines/hotels monitoring competitor rates
- Subscription services tracking competitive feature additions
- Retailers managing competitive positioning

**What you get:**
- Scheduled scraping system (daily, hourly, custom intervals)
- Price history database with trend analysis
- Alert system for significant changes (Slack, email, SMS)
- Dashboard visualizing competitor pricing/inventory over time
- CSV exports for analysis
- Legal compliance review (ensuring robots.txt and ToS compliance)

**Timeline:** 2–3 business days  
**Investment:** **$1,500 + $50/month maintenance**

---

### L. Data Cleaning & Migration

Transform messy, inconsistent datasets into clean, standardized, analysis-ready data.

**Who needs this:**
- Companies migrating between CRMs
- Businesses consolidating data from multiple sources
- Teams preparing lists for cold calling/outreach
- Organizations dealing with duplicate customer records
- Anyone with "bad data" blocking business operations

**What you get:**
- Audit of data quality issues
- Automated cleaning: phone formatting, address standardization, duplicate removal
- Validation rules and error reporting
- Cleaned CSV/Excel output ready for analysis
- Documentation of transformations applied
- Repeatable process if data arrives regularly

**Timeline:** 1–2 business days  
**Investment:** **$800 - $1,500** (depending on dataset size and complexity)

---

## Premium Bundles

**For clients ready to build complete AI/data infrastructure:**

### Bundle 1: "AI-Powered Operations" ($8,000 - $12,000)

**Best for:** Sales teams and lead-driven businesses

- Custom RAG Agent (Item A) — Handle customer inquiries automatically
- Multi-Agent Workflow (Item B) — Automate prospecting pipeline
- Lead Scoring System (Item F) — Prioritize high-value leads
- Includes: 30-day free support, managed hosting option

---

### Bundle 2: "Complete Business Intelligence" ($8,000 - $13,000)

**Best for:** Growth-stage companies and agencies

- Interactive Dashboard (Item D) — Real-time business metrics
- Automated Reporting Pipeline (Item E) — Weekly stakeholder reports
- Marketing Attribution Analysis (Item I) — Understand what drives revenue
- Includes: 30-day free support, custom metrics as needed

---

### Bundle 3: "Data Modernization" ($10,000 - $18,000)

**Best for:** Companies with legacy systems

- Excel to Web App Modernization (Item J) — Replace broken spreadsheets
- Automated Reporting Pipeline (Item E) — Eliminate manual work
- Predictive Analytics (Item F) — Data-driven decision making
- Includes: Full team training, 60-day free support

---

## Engagement Model

### **How I Work**

**Week 1:** 
- 1-hour discovery call (understand your exact business problem)
- Written requirements document and technical specifications
- 50% deposit, start date agreed

**Week 2-3:** 
- Daily development with async updates (Slack, email)
- Code pushed to private Git repository (you have visibility)
- Staging review — you see everything before production

**Week 4:** 
- Final testing and production deployment
- 1-hour video walkthrough of your new system
- Full documentation + source code handover

**Month 2-3:**
- Free bug fixes and minor adjustments (included)
- Slack/email support for questions
- Small tweaks and optimizations

---

## Deployment Options

### **1. Code Handover (Included)**
- Full source code + Git repository
- Installation guide and deployment scripts
- Video walkthrough + documentation
- You deploy to AWS, Render, Vercel, or your own infrastructure
- **Cost:** Included in project price

### **2. Managed Hosting (Optional)**
- I deploy and manage your solution on secure infrastructure
- Automatic backups, monitoring, and uptime alerts
- Minor updates and patches included
- 99.9% uptime SLA
- **Cost:** $50-150/month depending on scale (first 30 days free)

---

## Why Choose Me?

### **1. Certified Expert, Not a Junior**
- Google Data Analytics, IBM AI Engineer, Microsoft, Vanderbilt certifications
- 300+ automated tests per project (enterprise-grade quality assurance)
- Production-ready code on day one — no "learning on your dime"

### **2. Business-Focused Engineering**
I don't optimize for technical complexity — I optimize for **your revenue and time saved**:
- RAG agents reduce support tickets by 60%+
- Dashboards surface hidden business opportunities
- Automation frees up your team to do high-value work
- Every project has measurable ROI

### **3. No Surprises. No Tech Debt.**
- Complete documentation means future developers understand the code
- Automated test coverage prevents post-launch fires
- Architecture built to scale with your business
- If you need changes later, any developer can make them safely

### **4. Limited Availability = Focused Attention**
I only take 2-3 projects per quarter. Your project isn't one of 15 I'm juggling. You get my best work, not my leftover hours.

---

## Pricing Philosophy

I charge **fair market rates for senior-level AI engineering work** (not discount rates). Here's why:

- **You get what you pay for.** Cheap freelancers cut corners. My work doesn't break at 3am.
- **This filters out tire-kickers.** Serious businesses hire based on value, not cost. We're aligned on quality.
- **Your time is valuable.** Bad code costs you 10x what you saved on hire. My work is an investment, not an expense.

---

## Next Steps

**Ready to build something?**

1. **Email or message** with your project challenge
2. **15-minute call** to understand your situation
3. **Written proposal** within 24 hours
4. **Start immediately** if it's a fit

I'm currently accepting Q1 2026 projects. Given limited availability, **serious inquiries get priority.**

---

**Contact:** Cayman Roden  
Available via Upwork messaging, LinkedIn DM, or direct email.  
**Response time:** Same day (PST timezone)
"""

    pdf_generator = ServiceCatalogPDF("Service_Catalog.pdf")
    pdf_generator.build_pdf(markdown_content)
    print(f"✓ PDF generated successfully: Service_Catalog.pdf")


if __name__ == "__main__":
    main()




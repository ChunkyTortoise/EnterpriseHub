#!/usr/bin/env python3
"""
Generate 27 product images for Gumroad and Fiverr listings.

Requirements:
- PIL (Pillow) for image creation
- matplotlib for charts/diagrams
"""

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

# Output directory
OUTPUT_DIR = Path("/Users/cave/Documents/GitHub/EnterpriseHub/output/launch-images")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Color palettes
COLORS = {
    "primary": "#2563EB",  # Blue
    "secondary": "#7C3AED",  # Purple
    "accent": "#F59E0B",  # Orange
    "success": "#10B981",  # Green
    "dark": "#1F2937",  # Dark gray
    "light": "#F3F4F6",  # Light gray
    "white": "#FFFFFF",
}


def create_gradient_background(width, height, color1, color2):
    """Create a gradient background image."""
    base = Image.new("RGB", (width, height), color1)
    draw = ImageDraw.Draw(base)

    for y in range(height):
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

        ratio = y / height
        r = int(r1 + (r2 - r1) * ratio)
        g = int(g1 + (g2 - g1) * ratio)
        b = int(b1 + (b2 - b1) * ratio)

        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return base


def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple."""
    return tuple(int(hex_color[i : i + 2], 16) for i in (1, 3, 5))


def add_text_with_shadow(draw, position, text, font, fill, shadow_offset=3):
    """Add text with shadow effect."""
    x, y = position
    # Shadow
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=(0, 0, 0, 128))
    # Main text
    draw.text((x, y), text, font=font, fill=fill)


# ============================================================================
# GUMROAD THUMBNAILS (1200x630px)
# ============================================================================


def create_gumroad_docqa():
    """Create Gumroad thumbnail for DocQA Engine."""
    img = create_gradient_background(1200, 630, COLORS["primary"], COLORS["secondary"])
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 80)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 40)
        feature_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        feature_font = ImageFont.load_default()

    # Title
    add_text_with_shadow(draw, (60, 80), "AI Document", title_font, COLORS["white"])
    add_text_with_shadow(draw, (60, 170), "Q&A Engine", title_font, COLORS["white"])

    # Subtitle
    draw.text((60, 280), "Build RAG pipelines in hours, not weeks", font=subtitle_font, fill=COLORS["light"])

    # Features
    features = ["✓ Hybrid BM25 + Vector Search", "✓ 5 Chunking Strategies", "✓ Citation Scoring Built-In"]
    y = 370
    for feature in features:
        draw.text((60, y), feature, font=feature_font, fill=COLORS["white"])
        y += 50

    # Price badge
    badge_rect = [(950, 480), (1140, 580)]
    draw.rounded_rectangle(badge_rect, radius=15, fill=COLORS["accent"])
    price_font = (
        ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 50)
        if title_font != ImageFont.load_default()
        else title_font
    )
    draw.text((1000, 510), "$49", font=price_font, fill=COLORS["white"])

    img.save(OUTPUT_DIR / "gumroad-docqa-engine.png")
    print("✓ Created gumroad-docqa-engine.png")


def create_gumroad_agentforge():
    """Create Gumroad thumbnail for AgentForge."""
    img = create_gradient_background(1200, 630, COLORS["secondary"], COLORS["primary"])
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 80)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 40)
        feature_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        feature_font = ImageFont.load_default()

    # Title
    add_text_with_shadow(draw, (60, 80), "AgentForge", title_font, COLORS["white"])
    add_text_with_shadow(draw, (60, 170), "Multi-LLM", title_font, COLORS["white"])

    # Subtitle
    draw.text((60, 280), "Claude, Gemini, OpenAI, Perplexity unified", font=subtitle_font, fill=COLORS["light"])

    # Features
    features = ["✓ Unified Async Interface", "✓ Token-Aware Rate Limiting", "✓ Cost Tracking Built-In"]
    y = 370
    for feature in features:
        draw.text((60, y), feature, font=feature_font, fill=COLORS["white"])
        y += 50

    # Price badge
    badge_rect = [(950, 480), (1140, 580)]
    draw.rounded_rectangle(badge_rect, radius=15, fill=COLORS["accent"])
    price_font = (
        ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 50)
        if title_font != ImageFont.load_default()
        else title_font
    )
    draw.text((1000, 510), "$39", font=price_font, fill=COLORS["white"])

    img.save(OUTPUT_DIR / "gumroad-agentforge.png")
    print("✓ Created gumroad-agentforge.png")


def create_gumroad_scraper():
    """Create Gumroad thumbnail for Scrape-and-Serve."""
    img = create_gradient_background(1200, 630, COLORS["success"], COLORS["primary"])
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 70)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 40)
        feature_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        feature_font = ImageFont.load_default()

    # Title
    add_text_with_shadow(draw, (60, 80), "Web Scraper &", title_font, COLORS["white"])
    add_text_with_shadow(draw, (60, 160), "Price Monitor", title_font, COLORS["white"])

    # Subtitle
    draw.text((60, 270), "YAML config, price tracking, SEO scoring", font=subtitle_font, fill=COLORS["light"])

    # Features
    features = ["✓ YAML-Configurable", "✓ SHA-256 Change Detection", "✓ SEO Scoring (0-100)"]
    y = 370
    for feature in features:
        draw.text((60, y), feature, font=feature_font, fill=COLORS["white"])
        y += 50

    # Price badge
    badge_rect = [(950, 480), (1140, 580)]
    draw.rounded_rectangle(badge_rect, radius=15, fill=COLORS["accent"])
    price_font = (
        ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 50)
        if title_font != ImageFont.load_default()
        else title_font
    )
    draw.text((1000, 510), "$29", font=price_font, fill=COLORS["white"])

    img.save(OUTPUT_DIR / "gumroad-scraper.png")
    print("✓ Created gumroad-scraper.png")


def create_gumroad_dashboard():
    """Create Gumroad thumbnail for Insight Engine."""
    img = create_gradient_background(1200, 630, COLORS["accent"], COLORS["secondary"])
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 70)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 40)
        feature_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 28)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        feature_font = ImageFont.load_default()

    # Title
    add_text_with_shadow(draw, (60, 80), "Data Intelligence", title_font, COLORS["white"])
    add_text_with_shadow(draw, (60, 160), "Dashboard", title_font, COLORS["white"])

    # Subtitle
    draw.text((60, 270), "Upload → Dashboards & predictions in 30s", font=subtitle_font, fill=COLORS["light"])

    # Features
    features = ["✓ 4 Attribution Models", "✓ Predictive Modeling + SHAP", "✓ Auto-Generated PDF Reports"]
    y = 370
    for feature in features:
        draw.text((60, y), feature, font=feature_font, fill=COLORS["white"])
        y += 50

    # Price badge
    badge_rect = [(950, 480), (1140, 580)]
    draw.rounded_rectangle(badge_rect, radius=15, fill=COLORS["accent"])
    price_font = (
        ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 50)
        if title_font != ImageFont.load_default()
        else title_font
    )
    draw.text((1000, 510), "$39", font=price_font, fill=COLORS["white"])

    img.save(OUTPUT_DIR / "gumroad-dashboard.png")
    print("✓ Created gumroad-dashboard.png")


# ============================================================================
# FIVERR PRIMARY IMAGES (1280x769px)
# ============================================================================


def create_fiverr_rag_qa_primary():
    """Create Fiverr primary image for RAG Q&A gig."""
    img = create_gradient_background(1280, 769, COLORS["primary"], COLORS["dark"])
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 90)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 45)
        badge_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 35)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # Title
    add_text_with_shadow(draw, (60, 100), "RAG Document", title_font, COLORS["white"])
    add_text_with_shadow(draw, (60, 200), "Q&A System", title_font, COLORS["white"])

    # Subtitle
    draw.text((60, 330), "AI-powered document search with citations", font=subtitle_font, fill=COLORS["light"])

    # Stats badges
    badges = [("94%", "Precision"), ("322", "Tests"), ("$100+", "Starting")]
    x_start = 60
    for value, label in badges:
        badge_rect = [(x_start, 480), (x_start + 280, 600)]
        draw.rounded_rectangle(badge_rect, radius=15, fill=(255, 255, 255, 40))
        draw.text((x_start + 20, 500), value, font=title_font, fill=COLORS["accent"])
        draw.text((x_start + 20, 600), label, font=badge_font, fill=COLORS["white"])
        x_start += 320

    img.save(OUTPUT_DIR / "fiverr-rag-qa-primary.png")
    print("✓ Created fiverr-rag-qa-primary.png")


def create_fiverr_chatbot_primary():
    """Create Fiverr primary image for AI Chatbot gig."""
    img = create_gradient_background(1280, 769, COLORS["secondary"], COLORS["dark"])
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 90)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 45)
        badge_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 35)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # Title
    add_text_with_shadow(draw, (60, 100), "Multi-Agent", title_font, COLORS["white"])
    add_text_with_shadow(draw, (60, 200), "AI Chatbot", title_font, COLORS["white"])

    # Subtitle
    draw.text((60, 330), "Smart handoff & CRM integration", font=subtitle_font, fill=COLORS["light"])

    # Stats badges
    badges = [("94%", "Success"), ("4937", "Tests"), ("$200+", "Starting")]
    x_start = 60
    for value, label in badges:
        badge_rect = [(x_start, 480), (x_start + 280, 600)]
        draw.rounded_rectangle(badge_rect, radius=15, fill=(255, 255, 255, 40))
        draw.text((x_start + 20, 500), value, font=title_font, fill=COLORS["success"])
        draw.text((x_start + 20, 600), label, font=badge_font, fill=COLORS["white"])
        x_start += 320

    img.save(OUTPUT_DIR / "fiverr-chatbot-primary.png")
    print("✓ Created fiverr-chatbot-primary.png")


def create_fiverr_dashboard_primary():
    """Create Fiverr primary image for Data Dashboard gig."""
    img = create_gradient_background(1280, 769, COLORS["accent"], COLORS["dark"])
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 90)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 45)
        badge_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 35)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        badge_font = ImageFont.load_default()

    # Title
    add_text_with_shadow(draw, (60, 100), "Data Dashboard", title_font, COLORS["white"])
    add_text_with_shadow(draw, (60, 200), "from CSV/Excel", title_font, COLORS["white"])

    # Subtitle
    draw.text((60, 330), "Interactive charts in 30 seconds", font=subtitle_font, fill=COLORS["light"])

    # Stats badges
    badges = [("30s", "To Insights"), ("313", "Tests"), ("$50+", "Starting")]
    x_start = 60
    for value, label in badges:
        badge_rect = [(x_start, 480), (x_start + 280, 600)]
        draw.rounded_rectangle(badge_rect, radius=15, fill=(255, 255, 255, 40))
        draw.text((x_start + 20, 500), value, font=title_font, fill=COLORS["primary"])
        draw.text((x_start + 20, 600), label, font=badge_font, fill=COLORS["white"])
        x_start += 320

    img.save(OUTPUT_DIR / "fiverr-dashboard-primary.png")
    print("✓ Created fiverr-dashboard-primary.png")


# ============================================================================
# FIVERR GALLERY IMAGES (1280x769px)
# ============================================================================


def create_feature_showcase(filename, title, features, color_scheme):
    """Create a feature showcase image."""
    img = create_gradient_background(1280, 769, color_scheme[0], color_scheme[1])
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 70)
        feature_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 40)
    except OSError:
        title_font = ImageFont.load_default()
        feature_font = ImageFont.load_default()

    # Title
    add_text_with_shadow(draw, (60, 80), title, title_font, COLORS["white"])

    # Features
    y = 220
    for i, feature in enumerate(features, 1):
        # Number circle
        circle_rect = [(60, y), (120, y + 60)]
        draw.ellipse(circle_rect, fill=COLORS["accent"])
        draw.text((80, y + 10), str(i), font=title_font, fill=COLORS["white"])

        # Feature text
        draw.text((150, y + 10), feature, font=feature_font, fill=COLORS["white"])
        y += 100

    img.save(OUTPUT_DIR / filename)
    print(f"✓ Created {filename}")


def create_architecture_diagram(filename, title, components, color):
    """Create a simple architecture diagram using matplotlib."""
    fig, ax = plt.subplots(figsize=(16, 9.6))
    fig.patch.set_facecolor("#1F2937")
    ax.set_facecolor("#1F2937")
    ax.axis("off")

    # Title
    ax.text(0.5, 0.95, title, ha="center", va="top", fontsize=40, color="white", weight="bold", transform=ax.transAxes)

    # Draw components as boxes
    num_components = len(components)
    for i, component in enumerate(components):
        x = (i + 1) / (num_components + 1)
        y = 0.5

        # Box
        rect = mpatches.FancyBboxPatch(
            (x - 0.12, y - 0.15),
            0.24,
            0.3,
            boxstyle="round,pad=0.02",
            edgecolor=color,
            facecolor=color,
            linewidth=3,
            transform=ax.transAxes,
        )
        ax.add_patch(rect)

        # Text
        ax.text(
            x, y, component, ha="center", va="center", fontsize=28, color="white", weight="bold", transform=ax.transAxes
        )

        # Arrows
        if i < num_components - 1:
            next_x = (i + 2) / (num_components + 1)
            ax.annotate(
                "",
                xy=(next_x - 0.12, y),
                xytext=(x + 0.12, y),
                arrowprops=dict(arrowstyle="->", lw=3, color="white"),
                transform=ax.transAxes,
            )

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=100, facecolor="#1F2937")
    plt.close()
    print(f"✓ Created {filename}")


def create_comparison_chart(filename, title, items, scores, color):
    """Create a comparison bar chart using matplotlib."""
    fig, ax = plt.subplots(figsize=(16, 9.6))
    fig.patch.set_facecolor("#1F2937")
    ax.set_facecolor("#1F2937")

    # Title
    fig.suptitle(title, fontsize=40, color="white", weight="bold", y=0.95)

    # Bar chart
    y_pos = np.arange(len(items))
    bars = ax.barh(y_pos, scores, color=color, height=0.6)

    # Labels
    ax.set_yticks(y_pos)
    ax.set_yticklabels(items, fontsize=30, color="white")
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=25, color="white")

    # Grid
    ax.grid(axis="x", color="white", alpha=0.2, linestyle="--")
    ax.set_axisbelow(True)

    # Remove spines
    for spine in ax.spines.values():
        spine.set_visible(False)

    # Add value labels
    for i, (bar, score) in enumerate(zip(bars, scores)):
        ax.text(score + 2, i, f"{score}%", va="center", fontsize=28, color="white", weight="bold")

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=100, facecolor="#1F2937")
    plt.close()
    print(f"✓ Created {filename}")


def create_screenshot_mockup(filename, title, subtitle, features, color):
    """Create a mockup screenshot with features."""
    img = create_gradient_background(1280, 769, color, COLORS["dark"])
    draw = ImageDraw.Draw(img, "RGBA")

    try:
        title_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 60)
        subtitle_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 35)
        feature_font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", 30)
    except OSError:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        feature_font = ImageFont.load_default()

    # Title
    add_text_with_shadow(draw, (60, 60), title, title_font, COLORS["white"])
    draw.text((60, 140), subtitle, font=subtitle_font, fill=COLORS["light"])

    # Browser mockup
    browser_rect = [(60, 220), (1220, 690)]
    draw.rounded_rectangle(browser_rect, radius=10, fill=COLORS["white"])

    # Browser chrome
    chrome_rect = [(60, 220), (1220, 270)]
    draw.rounded_rectangle(chrome_rect, radius=10, fill=COLORS["light"])

    # Browser dots
    for i, dot_color in enumerate([hex_to_rgb("#EF4444"), hex_to_rgb("#F59E0B"), hex_to_rgb("#10B981")]):
        draw.ellipse([(90 + i * 30, 235), (110 + i * 30, 255)], fill=dot_color)

    # Features in content area
    y = 310
    for feature in features:
        draw.text((90, y), f"• {feature}", font=feature_font, fill=COLORS["dark"])
        y += 60

    img.save(OUTPUT_DIR / filename)
    print(f"✓ Created {filename}")


# ============================================================================
# RAG Q&A GALLERY (7 images)
# ============================================================================


def create_rag_gallery():
    """Create 7 gallery images for RAG Q&A gig."""

    # 1. Features showcase
    create_feature_showcase(
        "fiverr-rag-qa-features.png",
        "Key Features",
        [
            "Hybrid BM25 + Dense Vector Search",
            "5 Chunking Strategies Included",
            "Citation Scoring with Confidence",
            "Production REST API Built-In",
            "Evaluation Metrics Dashboard",
        ],
        (COLORS["primary"], COLORS["dark"]),
    )

    # 2. Architecture diagram
    create_architecture_diagram(
        "fiverr-rag-qa-architecture.png",
        "RAG Pipeline Architecture",
        ["Document\nIngestion", "Chunking\n& Embedding", "Vector\nStorage", "Hybrid\nRetrieval", "Answer\nGeneration"],
        COLORS["primary"],
    )

    # 3. Performance metrics
    create_comparison_chart(
        "fiverr-rag-qa-metrics.png",
        "Performance Metrics",
        ["Retrieval Precision", "Answer Relevance", "Citation Accuracy", "Response Speed"],
        [94, 89, 96, 95],
        COLORS["success"],
    )

    # 4. UI mockup
    create_screenshot_mockup(
        "fiverr-rag-qa-ui.png",
        "Streamlit Q&A Interface",
        "Ask questions, get cited answers instantly",
        [
            "Natural language queries",
            "Source citations with page numbers",
            "Confidence scores per answer",
            "Export to PDF report",
        ],
        COLORS["primary"],
    )

    # 5. API showcase
    create_feature_showcase(
        "fiverr-rag-qa-api.png",
        "REST API Endpoints",
        [
            "POST /documents - Upload PDFs",
            "POST /query - Ask questions",
            "GET /health - System status",
            "JWT auth + rate limiting",
            "100 req/min default",
        ],
        (COLORS["secondary"], COLORS["dark"]),
    )

    # 6. Chunking strategies
    create_feature_showcase(
        "fiverr-rag-qa-chunking.png",
        "5 Chunking Strategies",
        [
            "Fixed-size: Equal chunks",
            "Sentence: Natural boundaries",
            "Paragraph: Semantic grouping",
            "Recursive: Hierarchical",
            "Semantic: Context-aware",
        ],
        (COLORS["accent"], COLORS["dark"]),
    )

    # 7. Deployment options
    create_screenshot_mockup(
        "fiverr-rag-qa-deploy.png",
        "Deployment Ready",
        "Docker, Kubernetes, or cloud platform",
        ["Docker Compose included", "K8s manifests provided", "Zero-downtime updates", "Horizontal scaling support"],
        COLORS["success"],
    )


# ============================================================================
# CHATBOT GALLERY (7 images)
# ============================================================================


def create_chatbot_gallery():
    """Create 7 gallery images for AI Chatbot gig."""

    # 1. Features showcase
    create_feature_showcase(
        "fiverr-chatbot-features.png",
        "Multi-Agent System",
        [
            "3 Specialized Bot Personas",
            "Smart Context-Aware Handoff",
            "CRM Integration (GHL, HubSpot)",
            "Rate Limiting & Abuse Protection",
            "Analytics Dashboard Included",
        ],
        (COLORS["secondary"], COLORS["dark"]),
    )

    # 2. Architecture diagram
    create_architecture_diagram(
        "fiverr-chatbot-architecture.png",
        "Agent Swarm Architecture",
        ["Lead Bot", "Buyer Bot", "Seller Bot", "Handoff\nService", "CRM Sync"],
        COLORS["secondary"],
    )

    # 3. Performance metrics
    create_comparison_chart(
        "fiverr-chatbot-metrics.png",
        "Production Metrics",
        ["Handoff Success", "Intent Classification", "Context Preservation", "User Satisfaction"],
        [94, 94, 95, 96],
        COLORS["success"],
    )

    # 4. UI mockup
    create_screenshot_mockup(
        "fiverr-chatbot-ui.png",
        "Chat Interface",
        "Seamless conversations with smart handoff",
        ["Lead qualification bot", "Buyer assistance bot", "Seller consultation bot", "Human escalation option"],
        COLORS["secondary"],
    )

    # 5. CRM integration
    create_feature_showcase(
        "fiverr-chatbot-crm.png",
        "CRM Integration",
        [
            "GoHighLevel auto-sync",
            "HubSpot contact creation",
            "Salesforce webhook support",
            "Lead scoring & tagging",
            "Email notifications",
        ],
        (COLORS["primary"], COLORS["dark"]),
    )

    # 6. Handoff logic
    create_screenshot_mockup(
        "fiverr-chatbot-handoff.png",
        "Smart Handoff System",
        "Context-aware agent transitions",
        [
            "0.7 confidence threshold",
            "Circular handoff prevention",
            "Rate limiting (3/hr, 10/day)",
            "Pattern learning from history",
        ],
        COLORS["accent"],
    )

    # 7. Analytics dashboard
    create_screenshot_mockup(
        "fiverr-chatbot-analytics.png",
        "Analytics Dashboard",
        "Track conversations and conversions",
        ["Conversation volume by bot", "Lead scoring distribution", "Handoff success rates", "P50/P95/P99 latency"],
        COLORS["success"],
    )


# ============================================================================
# DASHBOARD GALLERY (6 images)
# ============================================================================


def create_dashboard_gallery():
    """Create 6 gallery images for Data Dashboard gig."""

    # 1. Features showcase
    create_feature_showcase(
        "fiverr-dashboard-features.png",
        "Intelligence Features",
        [
            "Auto-Profiler with Quality Scores",
            "4 Marketing Attribution Models",
            "Predictive Modeling + SHAP",
            "Time Series Forecasting",
            "PDF Export with Branding",
        ],
        (COLORS["accent"], COLORS["dark"]),
    )

    # 2. Workflow diagram
    create_architecture_diagram(
        "fiverr-dashboard-workflow.png",
        "Data to Insights Workflow",
        ["Upload\nCSV/Excel", "Auto\nProfile", "Generate\nCharts", "ML\nPredict", "Export\nPDF"],
        COLORS["accent"],
    )

    # 3. Performance metrics
    create_comparison_chart(
        "fiverr-dashboard-performance.png",
        "Speed & Accuracy",
        ["Time to Dashboard", "Chart Accuracy", "Auto-Detection", "Mobile Performance"],
        [95, 99, 91, 92],
        COLORS["success"],
    )

    # 4. UI mockup
    create_screenshot_mockup(
        "fiverr-dashboard-ui.png",
        "Interactive Dashboard",
        "Drag & drop your data, get insights instantly",
        [
            "Upload CSV, Excel, or JSON",
            "15+ chart types available",
            "Interactive filters & drill-down",
            "Export to PNG, PDF, HTML",
        ],
        COLORS["accent"],
    )

    # 5. ML models
    create_feature_showcase(
        "fiverr-dashboard-ml.png",
        "ML Capabilities",
        [
            "Classification & Regression",
            "SHAP Explanations",
            "Clustering (K-means)",
            "Time Series (ARIMA/Prophet)",
            "Anomaly Detection",
        ],
        (COLORS["primary"], COLORS["dark"]),
    )

    # 6. Export options
    create_screenshot_mockup(
        "fiverr-dashboard-export.png",
        "Professional Reports",
        "Auto-generated PDF reports with branding",
        ["Executive summary", "Data quality profile", "Charts and visualizations", "Model explanations & insights"],
        COLORS["secondary"],
    )


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Generate all 27 images."""
    print("🎨 Generating 27 product images...\n")

    print("📦 Gumroad Thumbnails (4):")
    create_gumroad_docqa()
    create_gumroad_agentforge()
    create_gumroad_scraper()
    create_gumroad_dashboard()

    print("\n🎯 Fiverr Primary Images (3):")
    create_fiverr_rag_qa_primary()
    create_fiverr_chatbot_primary()
    create_fiverr_dashboard_primary()

    print("\n🖼️  Fiverr Gallery Images (20):")
    print("\nRAG Q&A Gallery (7):")
    create_rag_gallery()

    print("\nChatbot Gallery (7):")
    create_chatbot_gallery()

    print("\nDashboard Gallery (6):")
    create_dashboard_gallery()

    print("\n" + "=" * 60)
    print("✅ All 27 images created successfully!")
    print(f"📁 Output directory: {OUTPUT_DIR}")

    # Summary
    total_size = sum(f.stat().st_size for f in OUTPUT_DIR.glob("*.png"))
    file_count = len(list(OUTPUT_DIR.glob("*.png")))

    print(f"\n📊 Summary:")
    print(f"   Images created: {file_count}")
    print(f"   Total size: {total_size / 1024 / 1024:.2f} MB")
    print("=" * 60)


if __name__ == "__main__":
    main()

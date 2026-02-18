#!/usr/bin/env python3
"""Generate professional 16:9 cover images for Contra services using PIL."""

from PIL import Image, ImageDraw, ImageFont
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../content/contra/covers")
os.makedirs(OUTPUT_DIR, exist_ok=True)

W, H = 1600, 900


def make_gradient(draw, color_top, color_bottom):
    for y in range(H):
        t = y / H
        r = int(color_top[0] + (color_bottom[0] - color_top[0]) * t)
        g = int(color_top[1] + (color_bottom[1] - color_top[1]) * t)
        b = int(color_top[2] + (color_bottom[2] - color_top[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))


def get_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def draw_pill(draw, x, y, text, bg, fg, font):
    bbox = font.getbbox(text)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad_x, pad_y = 24, 12
    rx, ry = x, y
    draw.rounded_rectangle([rx, ry, rx + tw + pad_x * 2, ry + th + pad_y * 2], radius=20, fill=bg)
    draw.text((rx + pad_x, ry + pad_y), text, fill=fg, font=font)
    return rx + tw + pad_x * 2 + 16  # next x


def draw_accent_bar(draw, color):
    draw.rectangle([80, H - 12, W - 80, H - 6], fill=color)


def make_service1():
    """Dashboard cover — dark blue/navy, charts theme."""
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    make_gradient(draw, (10, 18, 45), (20, 40, 90))

    # Decorative chart bars (right side)
    bar_colors = [(64, 130, 255), (90, 160, 255), (50, 110, 230), (100, 180, 255)]
    bar_w = 48
    bar_x = W - 300
    heights = [220, 340, 180, 400]
    for i, (h, c) in enumerate(zip(heights, bar_colors)):
        bx = bar_x + i * (bar_w + 20)
        draw.rounded_rectangle([bx, H // 2 + 80 - h, bx + bar_w, H // 2 + 80], radius=6, fill=c + (180,))

    # Glowing circle accent
    for r in range(120, 0, -10):
        alpha = int(15 * (1 - r / 120))
        draw.ellipse([W - 380 - r, 60 - r, W - 380 + r, 60 + r], fill=(64, 130, 255))

    # Title
    font_xl = get_font(72, bold=True)
    font_lg = get_font(40)
    font_sm = get_font(26)
    font_tag = get_font(22)

    draw.text((80, 120), "Custom Python", fill=(255, 255, 255), font=font_xl)
    draw.text((80, 210), "Data Dashboard", fill=(64, 130, 255), font=font_xl)

    draw.text((80, 320), "Turn your CSV/Excel into an interactive\nbusiness intelligence dashboard.", fill=(180, 200, 240), font=font_lg)

    # Metrics row
    metrics = ["313 Automated Tests", "100K rows in <500ms", "Full Source Code"]
    x = 80
    for m in metrics:
        x = draw_pill(draw, x, 460, m, (30, 70, 160), (180, 210, 255), get_font(22))

    # Pricing
    draw.text((80, 560), "Starting at $50 · 3-Day Delivery", fill=(100, 150, 220), font=font_sm)

    # Bottom tag line
    draw.text((80, H - 80), "Python  ·  Streamlit  ·  Plotly  ·  Pandas", fill=(80, 120, 180), font=font_tag)
    draw_accent_bar(draw, (64, 130, 255))

    img.save(os.path.join(OUTPUT_DIR, "service1-dashboard.jpg"), "JPEG", quality=95)
    print("✓ service1-dashboard.jpg")


def make_service2():
    """RAG/DocQA cover — deep purple, document/search theme."""
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    make_gradient(draw, (18, 10, 45), (50, 20, 90))

    # Document icon (right)
    doc_x, doc_y = W - 340, 80
    draw.rounded_rectangle([doc_x, doc_y, doc_x + 220, doc_y + 280], radius=12, fill=(60, 30, 120))
    for i in range(5):
        lx = doc_x + 24
        ly = doc_y + 50 + i * 42
        draw.rounded_rectangle([lx, ly, lx + 172, ly + 12], radius=6,
                                fill=(130, 80, 220) if i == 0 else (80, 50, 140))
    # Magnifier
    cx, cy, cr = doc_x + 200, doc_y + 240, 44
    draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(130, 80, 220))
    draw.ellipse([cx - cr + 8, cy - cr + 8, cx + cr - 8, cy + cr - 8], fill=(50, 20, 90))
    draw.line([cx + 28, cy + 28, cx + 55, cy + 55], fill=(180, 130, 255), width=8)

    font_xl = get_font(68, bold=True)
    font_lg = get_font(38)
    font_sm = get_font(26)
    font_tag = get_font(22)

    draw.text((80, 120), "AI Document Search", fill=(255, 255, 255), font=font_xl)
    draw.text((80, 210), "& Q&A with Citations", fill=(160, 100, 255), font=font_xl)

    draw.text((80, 320), "Ask questions in plain English — get precise\nanswers with exact source citations.", fill=(190, 170, 230), font=font_lg)

    metrics = ["94% Retrieval Precision", "RAGAS Score: 0.89", "322 Tests"]
    x = 80
    for m in metrics:
        x = draw_pill(draw, x, 460, m, (60, 20, 130), (200, 160, 255), get_font(22))

    draw.text((80, 560), "Starting at $100 · 3-Day Delivery", fill=(130, 90, 200), font=font_sm)
    draw.text((80, H - 80), "Python  ·  RAG  ·  ChromaDB  ·  FastAPI  ·  Streamlit", fill=(100, 70, 160), font=font_tag)
    draw_accent_bar(draw, (130, 80, 220))

    img.save(os.path.join(OUTPUT_DIR, "service2-rag.jpg"), "JPEG", quality=95)
    print("✓ service2-rag.jpg")


def make_service3():
    """Chatbot/CRM cover — dark teal/green, chat bubbles theme."""
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    make_gradient(draw, (8, 30, 35), (10, 60, 65))

    # Chat bubbles (right side)
    bubbles = [
        (W - 380, 100, 280, 50, (20, 100, 110), True),
        (W - 320, 180, 200, 50, (15, 70, 80), False),
        (W - 360, 260, 240, 50, (20, 100, 110), True),
        (W - 300, 340, 180, 50, (15, 70, 80), False),
    ]
    for bx, by, bw, bh, bc, right in bubbles:
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=20, fill=bc)
        # tail
        if right:
            draw.polygon([(bx + bw - 20, by + bh), (bx + bw, by + bh + 16), (bx + bw - 40, by + bh)], fill=bc)

    font_xl = get_font(66, bold=True)
    font_lg = get_font(38)
    font_sm = get_font(26)
    font_tag = get_font(22)

    draw.text((80, 120), "AI Chatbot with", fill=(255, 255, 255), font=font_xl)
    draw.text((80, 210), "Lead Qualification", fill=(40, 200, 180), font=font_xl)
    draw.text((80, 295), "& CRM Integration", fill=(40, 200, 180), font=font_xl)

    draw.text((80, 400), "24/7 lead qualification with instant CRM sync\nto GoHighLevel, HubSpot, or Salesforce.", fill=(160, 210, 205), font=font_lg)

    metrics = ["4,937 Tests", "94% Handoff Rate", "<200ms Response"]
    x = 80
    for m in metrics:
        x = draw_pill(draw, x, 530, m, (15, 80, 80), (100, 230, 220), get_font(22))

    draw.text((80, 630), "Starting at $150 · 5-Day Delivery", fill=(60, 160, 150), font=font_sm)
    draw.text((80, H - 80), "Python  ·  FastAPI  ·  Claude AI  ·  GoHighLevel  ·  Redis", fill=(50, 120, 115), font=font_tag)
    draw_accent_bar(draw, (40, 200, 180))

    img.save(os.path.join(OUTPUT_DIR, "service3-chatbot.jpg"), "JPEG", quality=95)
    print("✓ service3-chatbot.jpg")


if __name__ == "__main__":
    make_service1()
    make_service2()
    make_service3()
    print(f"\nSaved to: {OUTPUT_DIR}")

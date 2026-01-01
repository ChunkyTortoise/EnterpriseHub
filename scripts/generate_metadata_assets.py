from PIL import Image, ImageDraw, ImageFont
import os

def create_og_image(width, height, filename):
    # Professional dark blue background
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)
    
    # Gradient/Blob effect
    draw.ellipse([(-200, -200), (600, 600)], fill='#1e1b4b')
    draw.ellipse([(width-600, height-600), (width+200, height+200)], fill='#1e1b4b')
    
    # Title
    font_main = ImageFont.load_default()
    # Try to load a real font for better look if possible
    font_paths = ["/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
    for path in font_paths:
        if os.path.exists(path):
            font_title = ImageFont.truetype(path, 80)
            font_sub = ImageFont.truetype(path, 40)
            font_points = ImageFont.truetype(path, 30)
            break
    else:
        font_title = font_main
        font_sub = font_main
        font_points = font_main

    draw.text((80, 100), "EnterpriseHub", fill="#818cf8", font=font_title)
    draw.text((80, 200), "Transform Complex AI Tasks\nInto Simple, Reliable Systems", fill="white", font=font_sub)
    
    # Key points
    points = [
        "✓ 10 Production Modules",
        "✓ 1,768+ Hours Certified",
        "✓ 323+ Automated Tests"
    ]
    for i, point in enumerate(points):
        draw.text((80, 350 + (i * 50)), point, fill="#a5b4fc", font=font_points)
    
    # Border
    draw.rectangle([(20, 20), (width-20, height-20)], outline="#334155", width=2)
    
    img.save(filename)
    print(f"OG Image saved to {filename}")

def create_favicon(filename, size=32):
    img = Image.new('RGB', (size, size), color='#4f46e5')
    draw = ImageDraw.Draw(img)
    
    # Draw a stylized 'E'
    font_path = "/System/Library/Fonts/Helvetica.ttc"
    if os.path.exists(font_path):
        font = ImageFont.truetype(font_path, int(size*0.8))
        draw.text((size//2, size//2), "E", fill="white", font=font, anchor="mm")
    else:
        draw.text((size//4, size//4), "E", fill="white")
    
    img.save(filename)
    print(f"Favicon saved to {filename}")

# Run
create_og_image(1200, 630, "portfolio/assets/images/og-image.jpg")
create_favicon("portfolio/assets/images/favicon-32x32.png", 32)
create_favicon("portfolio/assets/images/favicon-16x16.png", 16)
create_favicon("portfolio/assets/images/apple-touch-icon.png", 180)

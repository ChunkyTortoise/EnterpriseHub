from PIL import Image, ImageDraw, ImageFont
import os

def create_banner(width, height, filename, title, subtitle, accent_color="#4f46e5"):
    # Create background with gradient-like effect
    img = Image.new('RGB', (width, height), color='#0f172a')
    draw = ImageDraw.Draw(img)
    
    # Add some decorative elements (circles/blobs)
    draw.ellipse([(-100, -100), (300, 300)], fill='#1e1b4b')
    draw.ellipse([(width-300, height-300), (width+100, height+100)], fill='#1e1b4b')
    
    # Draw a simple grid for "technical" feel
    grid_spacing = 40
    for x in range(0, width, grid_spacing):
        draw.line([(x, 0), (x, height)], fill='#1e293b', width=1)
    for y in range(0, height, grid_spacing):
        draw.line([(0, y), (width, y)], fill='#1e293b', width=1)

    # Since I don't know where the fonts are on this system, I'll use the default font
    # but I'll try to load a common one if available
    font_paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"
    ]
    
    font_main = None
    font_sub = None
    
    for path in font_paths:
        if os.path.exists(path):
            try:
                font_main = ImageFont.truetype(path, 60)
                font_sub = ImageFont.truetype(path, 30)
                break
            except:
                continue
    
    if font_main is None:
        font_main = ImageFont.load_default()
        font_sub = ImageFont.load_default()

    # Draw Text
    # Title
    draw.text((width//2, height//2 - 40), title, fill="white", font=font_main, anchor="mm")
    # Subtitle
    draw.text((width//2, height//2 + 40), subtitle, fill="#a5b4fc", font=font_sub, anchor="mm")
    
    # Add a "badge" or line
    draw.line([(width//2 - 100, height//2 + 80), (width//2 + 100, height//2 + 80)], fill=accent_color, width=4)
    
    img.save(filename)
    print(f"Banner saved to {filename}")

# LinkedIn Banner
create_banner(1584, 396, "portfolio/assets/images/linkedin-banner.png", 
              "EnterpriseHub", "AI Technical Co-Founder | Agentic Workflows")

# Upwork Banner (standard size varies, but let's go with 1600x400)
create_banner(1600, 400, "portfolio/assets/images/upwork-banner.png", 
              "Autonomous Agent Architect", "Building self-evolving AI systems that scale.")

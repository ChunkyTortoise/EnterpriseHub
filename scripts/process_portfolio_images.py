from PIL import Image
import os

mappings = {
    "Screenshot_1.jpg": "portfolio/assets/images/platform-overview.png",
    "Screenshot_4.jpg": "portfolio/assets/images/market-pulse.png",
    "Screenshot_6.jpg": "portfolio/assets/images/design-system.png",
    "Screenshot_5.jpg": "portfolio/assets/images/content-engine.png",
    "Screenshot_2.jpg": "portfolio/assets/images/financial-analyst.png",
    "Screenshot_3.jpg": "portfolio/assets/images/margin-hunter.png",
}

for src, dst in mappings.items():
    if os.path.exists(src):
        print(f"Converting {src} to {dst}...")
        img = Image.open(src)
        img.save(dst, "PNG")
    else:
        print(f"Source {src} not found.")

print("Screenshot conversion complete.")

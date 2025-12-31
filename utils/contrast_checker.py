"""
WCAG Contrast Ratio Checker for UI Theme Colors.

Verifies that all text/background color combinations meet WCAG AAA standards.
"""

from typing import Tuple


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate relative luminance for RGB color."""
    r, g, b = [x / 255.0 for x in rgb]

    # Apply gamma correction
    def adjust(channel: float) -> float:
        if channel <= 0.03928:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    r, g, b = adjust(r), adjust(g), adjust(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color1: str, color2: str) -> float:
    """Calculate contrast ratio between two hex colors."""
    lum1 = relative_luminance(hex_to_rgb(color1))
    lum2 = relative_luminance(hex_to_rgb(color2))

    lighter = max(lum1, lum2)
    darker = min(lum1, lum2)

    return (lighter + 0.05) / (darker + 0.05)


def check_wcag_compliance(foreground: str, background: str, level: str = "AAA") -> dict:
    """
    Check if color combination meets WCAG standards.

    Args:
        foreground: Hex color code for text
        background: Hex color code for background
        level: "AA" or "AAA" (default: AAA)

    Returns:
        dict with compliance status and ratio
    """
    ratio = contrast_ratio(foreground, background)

    # WCAG standards
    standards = {
        "AAA": {"normal": 7.0, "large": 4.5},
        "AA": {"normal": 4.5, "large": 3.0},
    }

    required = standards.get(level, standards["AAA"])

    return {
        "ratio": round(ratio, 2),
        "passes_normal": ratio >= required["normal"],
        "passes_large": ratio >= required["large"],
        "level": level,
        "foreground": foreground,
        "background": background,
    }


def audit_theme(theme: dict) -> None:
    """Audit entire theme for WCAG AAA compliance."""
    print("\n=== WCAG AAA Contrast Audit ===\n")

    # Test combinations
    tests = [
        ("Primary text on background", theme["text_main"], theme["background"]),
        ("Light text on background", theme["text_light"], theme["background"]),
        ("Primary text on surface", theme["text_main"], theme["surface"]),
        ("Light text on surface", theme["text_light"], theme["surface"]),
        ("Primary color on background", theme["primary"], theme["background"]),
        ("Success text on background", theme["success"], theme["background"]),
        ("Danger text on background", theme["danger"], theme["background"]),
        ("White text on primary", "#FFFFFF", theme["primary"]),
    ]

    failures = []

    for name, fg, bg in tests:
        result = check_wcag_compliance(fg, bg, "AAA")
        status = "✓ PASS" if result["passes_normal"] else "✗ FAIL"

        print(f"{status} | {name}")
        print(f"         Ratio: {result['ratio']}:1 (need 7:1 for normal text)")

        if not result["passes_normal"]:
            failures.append((name, result))
            print("         ⚠️  Consider adjusting colors")
        print()

    if failures:
        print(f"\n⚠️  {len(failures)} combinations failed AAA compliance")
        print("Recommendations:")
        for name, result in failures:
            if result["ratio"] < 4.5:
                print(f"  • {name}: Increase contrast significantly")
            elif result["ratio"] < 7.0:
                print(f"  • {name}: Slight adjustment needed (currently {result['ratio']}:1)")
    else:
        print("✓ All combinations pass WCAG AAA!")


if __name__ == "__main__":
    # Import theme from ui.py
    import os
    import sys

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.ui import DARK_THEME, LIGHT_THEME

    print("\n" + "=" * 50)
    print("LIGHT THEME AUDIT")
    print("=" * 50)
    audit_theme(LIGHT_THEME)

    print("\n" + "=" * 50)
    print("DARK THEME AUDIT")
    print("=" * 50)
    audit_theme(DARK_THEME)

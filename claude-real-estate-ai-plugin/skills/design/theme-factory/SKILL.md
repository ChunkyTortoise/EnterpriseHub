---
name: Theme Factory
description: This skill should be used when implementing "professional styling", "theme systems", "brand consistency", "design tokens", "visual identity", "color schemes", "typography systems", or when creating cohesive visual themes for applications.
version: 1.0.0
---

# Theme Factory: Professional Styling and Theming

## Overview

This skill provides comprehensive theming capabilities for creating professional, brand-consistent visual identities across applications. It includes theme generators, design token management, and automated styling systems specifically optimized for Streamlit applications.

## When to Use This Skill

Use this skill when implementing:
- **Professional brand themes** and visual identities
- **Multi-theme support** and theme switching
- **Design token systems** for consistent styling
- **Dark/light mode** implementations
- **Industry-specific themes** (real estate, finance, healthcare)
- **Custom brand guidelines** and style systems
- **Responsive theme adaptations**

## Core Theming System

### 1. Theme Architecture

```python
"""
Comprehensive theme architecture with design tokens and variants
"""

from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import json
from pathlib import Path
import colorsys
import streamlit as st


class ThemeCategory(Enum):
    """Categories of themes for different use cases."""
    BUSINESS_PROFESSIONAL = "business_professional"
    REAL_ESTATE = "real_estate"
    FINANCE = "finance"
    HEALTHCARE = "healthcare"
    TECHNOLOGY = "technology"
    CREATIVE = "creative"
    MINIMAL = "minimal"
    LUXURY = "luxury"


class ThemeMode(Enum):
    """Theme mode variations."""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"


class ColorIntensity(Enum):
    """Color intensity levels for theme variations."""
    SUBTLE = "subtle"
    MODERATE = "moderate"
    VIBRANT = "vibrant"
    BOLD = "bold"


@dataclass
class ColorPalette:
    """Comprehensive color palette with semantic meanings."""
    # Primary brand colors
    primary_50: str
    primary_100: str
    primary_200: str
    primary_300: str
    primary_400: str
    primary_500: str  # Main brand color
    primary_600: str
    primary_700: str
    primary_800: str
    primary_900: str

    # Secondary colors
    secondary_50: str
    secondary_100: str
    secondary_200: str
    secondary_300: str
    secondary_400: str
    secondary_500: str
    secondary_600: str
    secondary_700: str
    secondary_800: str
    secondary_900: str

    # Accent colors
    accent_50: str
    accent_100: str
    accent_200: str
    accent_300: str
    accent_400: str
    accent_500: str
    accent_600: str
    accent_700: str
    accent_800: str
    accent_900: str

    # Semantic colors
    success: str
    success_light: str
    success_dark: str

    warning: str
    warning_light: str
    warning_dark: str

    error: str
    error_light: str
    error_dark: str

    info: str
    info_light: str
    info_dark: str

    # Neutral colors
    neutral_0: str   # Pure white
    neutral_50: str
    neutral_100: str
    neutral_200: str
    neutral_300: str
    neutral_400: str
    neutral_500: str
    neutral_600: str
    neutral_700: str
    neutral_800: str
    neutral_900: str
    neutral_950: str # Near black


@dataclass
class TypographyScale:
    """Typography scale with consistent sizing and hierarchy."""
    # Font families
    font_family_primary: str
    font_family_secondary: str
    font_family_mono: str

    # Font sizes
    text_xs: str    # 12px
    text_sm: str    # 14px
    text_base: str  # 16px
    text_lg: str    # 18px
    text_xl: str    # 20px
    text_2xl: str   # 24px
    text_3xl: str   # 30px
    text_4xl: str   # 36px
    text_5xl: str   # 48px
    text_6xl: str   # 60px

    # Font weights
    font_weight_thin: str       # 100
    font_weight_extralight: str # 200
    font_weight_light: str      # 300
    font_weight_normal: str     # 400
    font_weight_medium: str     # 500
    font_weight_semibold: str   # 600
    font_weight_bold: str       # 700
    font_weight_extrabold: str  # 800
    font_weight_black: str      # 900

    # Line heights
    leading_none: str      # 1
    leading_tight: str     # 1.25
    leading_snug: str      # 1.375
    leading_normal: str    # 1.5
    leading_relaxed: str   # 1.625
    leading_loose: str     # 2

    # Letter spacing
    tracking_tighter: str  # -0.05em
    tracking_tight: str    # -0.025em
    tracking_normal: str   # 0em
    tracking_wide: str     # 0.025em
    tracking_wider: str    # 0.05em
    tracking_widest: str   # 0.1em


@dataclass
class SpacingScale:
    """Consistent spacing scale for layouts and components."""
    # Spacing values
    space_0: str    # 0px
    space_px: str   # 1px
    space_0_5: str  # 2px
    space_1: str    # 4px
    space_1_5: str  # 6px
    space_2: str    # 8px
    space_2_5: str  # 10px
    space_3: str    # 12px
    space_3_5: str  # 14px
    space_4: str    # 16px
    space_5: str    # 20px
    space_6: str    # 24px
    space_7: str    # 28px
    space_8: str    # 32px
    space_9: str    # 36px
    space_10: str   # 40px
    space_11: str   # 44px
    space_12: str   # 48px
    space_14: str   # 56px
    space_16: str   # 64px
    space_20: str   # 80px
    space_24: str   # 96px
    space_28: str   # 112px
    space_32: str   # 128px
    space_36: str   # 144px
    space_40: str   # 160px
    space_44: str   # 176px
    space_48: str   # 192px
    space_52: str   # 208px
    space_56: str   # 224px
    space_60: str   # 240px
    space_64: str   # 256px
    space_72: str   # 288px
    space_80: str   # 320px
    space_96: str   # 384px


@dataclass
class BorderRadiusScale:
    """Border radius scale for consistent component styling."""
    radius_none: str    # 0px
    radius_sm: str      # 2px
    radius: str         # 4px
    radius_md: str      # 6px
    radius_lg: str      # 8px
    radius_xl: str      # 12px
    radius_2xl: str     # 16px
    radius_3xl: str     # 24px
    radius_full: str    # 9999px


@dataclass
class ShadowScale:
    """Shadow scale for depth and elevation."""
    shadow_none: str
    shadow_sm: str
    shadow: str
    shadow_md: str
    shadow_lg: str
    shadow_xl: str
    shadow_2xl: str
    shadow_inner: str


@dataclass
class AnimationScale:
    """Animation and transition scale."""
    # Durations
    duration_75: str    # 75ms
    duration_100: str   # 100ms
    duration_150: str   # 150ms
    duration_200: str   # 200ms
    duration_300: str   # 300ms
    duration_500: str   # 500ms
    duration_700: str   # 700ms
    duration_1000: str  # 1000ms

    # Timing functions
    ease_linear: str
    ease_in: str
    ease_out: str
    ease_in_out: str


@dataclass
class ThemeDefinition:
    """Complete theme definition with all design tokens."""
    name: str
    category: ThemeCategory
    mode: ThemeMode
    description: str

    # Design token scales
    colors: ColorPalette
    typography: TypographyScale
    spacing: SpacingScale
    border_radius: BorderRadiusScale
    shadows: ShadowScale
    animations: AnimationScale

    # Theme metadata
    version: str = "1.0.0"
    author: Optional[str] = None
    created_at: Optional[str] = None
    tags: List[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert theme to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Convert theme to JSON string."""
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ThemeDefinition':
        """Create theme from dictionary."""
        # Extract nested dataclass fields
        colors = ColorPalette(**data['colors'])
        typography = TypographyScale(**data['typography'])
        spacing = SpacingScale(**data['spacing'])
        border_radius = BorderRadiusScale(**data['border_radius'])
        shadows = ShadowScale(**data['shadows'])
        animations = AnimationScale(**data['animations'])

        # Create theme definition
        return cls(
            name=data['name'],
            category=ThemeCategory(data['category']),
            mode=ThemeMode(data['mode']),
            description=data['description'],
            colors=colors,
            typography=typography,
            spacing=spacing,
            border_radius=border_radius,
            shadows=shadows,
            animations=animations,
            version=data.get('version', '1.0.0'),
            author=data.get('author'),
            created_at=data.get('created_at'),
            tags=data.get('tags', [])
        )


class ColorUtilities:
    """Utilities for color manipulation and palette generation."""

    @staticmethod
    def hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

    @staticmethod
    def rgb_to_hex(rgb: tuple) -> str:
        """Convert RGB to hex color."""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)

    @staticmethod
    def lighten_color(hex_color: str, factor: float) -> str:
        """Lighten a color by a factor (0-1)."""
        rgb = ColorUtilities.hex_to_rgb(hex_color)
        h, l, s = colorsys.rgb_to_hls(*[x/255.0 for x in rgb])
        l = min(1.0, l + factor)
        rgb = tuple(int(x * 255) for x in colorsys.hls_to_rgb(h, l, s))
        return ColorUtilities.rgb_to_hex(rgb)

    @staticmethod
    def darken_color(hex_color: str, factor: float) -> str:
        """Darken a color by a factor (0-1)."""
        rgb = ColorUtilities.hex_to_rgb(hex_color)
        h, l, s = colorsys.rgb_to_hls(*[x/255.0 for x in rgb])
        l = max(0.0, l - factor)
        rgb = tuple(int(x * 255) for x in colorsys.hls_to_rgb(h, l, s))
        return ColorUtilities.rgb_to_hex(rgb)

    @staticmethod
    def generate_palette(base_color: str) -> Dict[str, str]:
        """Generate a full color palette from a base color."""
        palette = {}

        # Generate lightness variations
        variations = [
            (50, 0.95),   # Very light
            (100, 0.90),  # Light
            (200, 0.80),
            (300, 0.70),
            (400, 0.60),
            (500, 0.50),  # Base color
            (600, 0.40),
            (700, 0.30),
            (800, 0.20),
            (900, 0.10),  # Very dark
        ]

        rgb = ColorUtilities.hex_to_rgb(base_color)
        h, l, s = colorsys.rgb_to_hls(*[x/255.0 for x in rgb])

        for weight, lightness in variations:
            new_rgb = tuple(int(x * 255) for x in colorsys.hls_to_rgb(h, lightness, s))
            palette[f"{weight}"] = ColorUtilities.rgb_to_hex(new_rgb)

        return palette

    @staticmethod
    def ensure_contrast(foreground: str, background: str, min_ratio: float = 4.5) -> str:
        """Ensure sufficient contrast between foreground and background colors."""
        # Simplified contrast adjustment
        fg_rgb = ColorUtilities.hex_to_rgb(foreground)
        bg_rgb = ColorUtilities.hex_to_rgb(background)

        # Calculate relative luminance
        def luminance(rgb):
            return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]

        fg_lum = luminance(fg_rgb)
        bg_lum = luminance(bg_rgb)

        # If contrast is insufficient, adjust foreground
        if abs(fg_lum - bg_lum) < min_ratio * 50:  # Simplified calculation
            if bg_lum > 127:  # Light background
                return ColorUtilities.darken_color(foreground, 0.3)
            else:  # Dark background
                return ColorUtilities.lighten_color(foreground, 0.3)

        return foreground


class ThemeFactory:
    """Factory for generating and managing themes."""

    def __init__(self):
        self.themes: Dict[str, ThemeDefinition] = {}
        self.current_theme: Optional[ThemeDefinition] = None

    def create_real_estate_theme(
        self,
        primary_color: str = "#1e40af",
        mode: ThemeMode = ThemeMode.LIGHT,
        intensity: ColorIntensity = ColorIntensity.MODERATE
    ) -> ThemeDefinition:
        """Create a professional real estate theme."""

        # Generate color palettes
        primary_palette = ColorUtilities.generate_palette(primary_color)

        # Define semantic colors based on real estate industry
        if mode == ThemeMode.LIGHT:
            colors = ColorPalette(
                # Primary palette (brand blue)
                primary_50=primary_palette["50"],
                primary_100=primary_palette["100"],
                primary_200=primary_palette["200"],
                primary_300=primary_palette["300"],
                primary_400=primary_palette["400"],
                primary_500=primary_palette["500"],
                primary_600=primary_palette["600"],
                primary_700=primary_palette["700"],
                primary_800=primary_palette["800"],
                primary_900=primary_palette["900"],

                # Secondary palette (warm gray)
                secondary_50="#fafaf9",
                secondary_100="#f5f5f4",
                secondary_200="#e7e5e4",
                secondary_300="#d6d3d1",
                secondary_400="#a8a29e",
                secondary_500="#78716c",
                secondary_600="#57534e",
                secondary_700="#44403c",
                secondary_800="#292524",
                secondary_900="#1c1917",

                # Accent palette (gold)
                accent_50="#fffbeb",
                accent_100="#fef3c7",
                accent_200="#fde68a",
                accent_300="#fcd34d",
                accent_400="#fbbf24",
                accent_500="#f59e0b",
                accent_600="#d97706",
                accent_700="#b45309",
                accent_800="#92400e",
                accent_900="#78350f",

                # Semantic colors
                success="#10b981",
                success_light="#d1fae5",
                success_dark="#047857",

                warning="#f59e0b",
                warning_light="#fef3c7",
                warning_dark="#d97706",

                error="#ef4444",
                error_light="#fecaca",
                error_dark="#dc2626",

                info="#3b82f6",
                info_light="#dbeafe",
                info_dark="#1d4ed8",

                # Neutral colors
                neutral_0="#ffffff",
                neutral_50="#fafafa",
                neutral_100="#f5f5f5",
                neutral_200="#e5e5e5",
                neutral_300="#d4d4d4",
                neutral_400="#a3a3a3",
                neutral_500="#737373",
                neutral_600="#525252",
                neutral_700="#404040",
                neutral_800="#262626",
                neutral_900="#171717",
                neutral_950="#0a0a0a",
            )
        else:  # Dark mode
            colors = ColorPalette(
                # Adjusted for dark mode
                primary_50="#1e293b",
                primary_100="#334155",
                primary_200="#475569",
                primary_300="#64748b",
                primary_400="#94a3b8",
                primary_500="#cbd5e1",
                primary_600="#e2e8f0",
                primary_700="#f1f5f9",
                primary_800="#f8fafc",
                primary_900="#ffffff",

                # Dark mode secondary
                secondary_50="#0f172a",
                secondary_100="#1e293b",
                secondary_200="#334155",
                secondary_300="#475569",
                secondary_400="#64748b",
                secondary_500="#94a3b8",
                secondary_600="#cbd5e1",
                secondary_700="#e2e8f0",
                secondary_800="#f1f5f9",
                secondary_900="#f8fafc",

                # Accent colors (adjusted)
                accent_50="#451a03",
                accent_100="#78350f",
                accent_200="#92400e",
                accent_300="#b45309",
                accent_400="#d97706",
                accent_500="#f59e0b",
                accent_600="#fbbf24",
                accent_700="#fcd34d",
                accent_800="#fde68a",
                accent_900="#fef3c7",

                # Dark mode semantic colors
                success="#059669",
                success_light="#064e3b",
                success_dark="#10b981",

                warning="#d97706",
                warning_light="#92400e",
                warning_dark="#f59e0b",

                error="#dc2626",
                error_light="#7f1d1d",
                error_dark="#ef4444",

                info="#1d4ed8",
                info_light="#1e3a8a",
                info_dark="#3b82f6",

                # Dark mode neutrals
                neutral_0="#0a0a0a",
                neutral_50="#171717",
                neutral_100="#262626",
                neutral_200="#404040",
                neutral_300="#525252",
                neutral_400="#737373",
                neutral_500="#a3a3a3",
                neutral_600="#d4d4d4",
                neutral_700="#e5e5e5",
                neutral_800="#f5f5f5",
                neutral_900="#fafafa",
                neutral_950="#ffffff",
            )

        # Typography optimized for real estate
        typography = TypographyScale(
            # Professional font families
            font_family_primary='"Inter", "SF Pro Display", -apple-system, BlinkMacSystemFont, system-ui, sans-serif',
            font_family_secondary='"Roboto", "Segoe UI", system-ui, sans-serif',
            font_family_mono='"JetBrains Mono", "SF Mono", "Monaco", "Consolas", monospace',

            # Font sizes
            text_xs="0.75rem",    # 12px
            text_sm="0.875rem",   # 14px
            text_base="1rem",     # 16px
            text_lg="1.125rem",   # 18px
            text_xl="1.25rem",    # 20px
            text_2xl="1.5rem",    # 24px
            text_3xl="1.875rem",  # 30px
            text_4xl="2.25rem",   # 36px
            text_5xl="3rem",      # 48px
            text_6xl="3.75rem",   # 60px

            # Font weights
            font_weight_thin="100",
            font_weight_extralight="200",
            font_weight_light="300",
            font_weight_normal="400",
            font_weight_medium="500",
            font_weight_semibold="600",
            font_weight_bold="700",
            font_weight_extrabold="800",
            font_weight_black="900",

            # Line heights
            leading_none="1",
            leading_tight="1.25",
            leading_snug="1.375",
            leading_normal="1.5",
            leading_relaxed="1.625",
            leading_loose="2",

            # Letter spacing
            tracking_tighter="-0.05em",
            tracking_tight="-0.025em",
            tracking_normal="0em",
            tracking_wide="0.025em",
            tracking_wider="0.05em",
            tracking_widest="0.1em",
        )

        # Consistent spacing scale
        spacing = SpacingScale(
            space_0="0px",
            space_px="1px",
            space_0_5="0.125rem",  # 2px
            space_1="0.25rem",     # 4px
            space_1_5="0.375rem",  # 6px
            space_2="0.5rem",      # 8px
            space_2_5="0.625rem",  # 10px
            space_3="0.75rem",     # 12px
            space_3_5="0.875rem",  # 14px
            space_4="1rem",        # 16px
            space_5="1.25rem",     # 20px
            space_6="1.5rem",      # 24px
            space_7="1.75rem",     # 28px
            space_8="2rem",        # 32px
            space_9="2.25rem",     # 36px
            space_10="2.5rem",     # 40px
            space_11="2.75rem",    # 44px
            space_12="3rem",       # 48px
            space_14="3.5rem",     # 56px
            space_16="4rem",       # 64px
            space_20="5rem",       # 80px
            space_24="6rem",       # 96px
            space_28="7rem",       # 112px
            space_32="8rem",       # 128px
            space_36="9rem",       # 144px
            space_40="10rem",      # 160px
            space_44="11rem",      # 176px
            space_48="12rem",      # 192px
            space_52="13rem",      # 208px
            space_56="14rem",      # 224px
            space_60="15rem",      # 240px
            space_64="16rem",      # 256px
            space_72="18rem",      # 288px
            space_80="20rem",      # 320px
            space_96="24rem",      # 384px
        )

        # Border radius scale
        border_radius = BorderRadiusScale(
            radius_none="0px",
            radius_sm="0.125rem",    # 2px
            radius="0.25rem",        # 4px
            radius_md="0.375rem",    # 6px
            radius_lg="0.5rem",      # 8px
            radius_xl="0.75rem",     # 12px
            radius_2xl="1rem",       # 16px
            radius_3xl="1.5rem",     # 24px
            radius_full="9999px",
        )

        # Shadow scale for depth
        shadows = ShadowScale(
            shadow_none="0 0 #0000",
            shadow_sm="0 1px 2px 0 rgb(0 0 0 / 0.05)",
            shadow="0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
            shadow_md="0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
            shadow_lg="0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
            shadow_xl="0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
            shadow_2xl="0 25px 50px -12px rgb(0 0 0 / 0.25)",
            shadow_inner="inset 0 2px 4px 0 rgb(0 0 0 / 0.05)",
        )

        # Animation scale
        animations = AnimationScale(
            duration_75="75ms",
            duration_100="100ms",
            duration_150="150ms",
            duration_200="200ms",
            duration_300="300ms",
            duration_500="500ms",
            duration_700="700ms",
            duration_1000="1000ms",

            ease_linear="linear",
            ease_in="cubic-bezier(0.4, 0, 1, 1)",
            ease_out="cubic-bezier(0, 0, 0.2, 1)",
            ease_in_out="cubic-bezier(0.4, 0, 0.2, 1)",
        )

        # Create theme definition
        theme = ThemeDefinition(
            name=f"Real Estate Professional ({mode.value.title()})",
            category=ThemeCategory.REAL_ESTATE,
            mode=mode,
            description="Professional theme designed for real estate applications with trust-building colors and clear typography.",
            colors=colors,
            typography=typography,
            spacing=spacing,
            border_radius=border_radius,
            shadows=shadows,
            animations=animations,
            tags=["professional", "real_estate", "blue", "clean", "trustworthy"]
        )

        return theme

    def create_luxury_real_estate_theme(
        self,
        mode: ThemeMode = ThemeMode.LIGHT
    ) -> ThemeDefinition:
        """Create a luxury real estate theme with gold accents."""

        if mode == ThemeMode.LIGHT:
            primary_color = "#1a1a1a"  # Deep charcoal
            secondary_color = "#d4af37"  # Gold
            accent_color = "#8b4513"  # Saddle brown
        else:
            primary_color = "#f8f8ff"  # Ghost white
            secondary_color = "#daa520"  # Goldenrod
            accent_color = "#cd853f"  # Peru

        # Generate luxury color palette
        primary_palette = ColorUtilities.generate_palette(primary_color)
        secondary_palette = ColorUtilities.generate_palette(secondary_color)
        accent_palette = ColorUtilities.generate_palette(accent_color)

        # Build luxury colors
        colors = ColorPalette(
            # Primary (charcoal/white)
            primary_50=primary_palette["50"],
            primary_100=primary_palette["100"],
            primary_200=primary_palette["200"],
            primary_300=primary_palette["300"],
            primary_400=primary_palette["400"],
            primary_500=primary_palette["500"],
            primary_600=primary_palette["600"],
            primary_700=primary_palette["700"],
            primary_800=primary_palette["800"],
            primary_900=primary_palette["900"],

            # Secondary (gold)
            secondary_50=secondary_palette["50"],
            secondary_100=secondary_palette["100"],
            secondary_200=secondary_palette["200"],
            secondary_300=secondary_palette["300"],
            secondary_400=secondary_palette["400"],
            secondary_500=secondary_palette["500"],
            secondary_600=secondary_palette["600"],
            secondary_700=secondary_palette["700"],
            secondary_800=secondary_palette["800"],
            secondary_900=secondary_palette["900"],

            # Accent (brown)
            accent_50=accent_palette["50"],
            accent_100=accent_palette["100"],
            accent_200=accent_palette["200"],
            accent_300=accent_palette["300"],
            accent_400=accent_palette["400"],
            accent_500=accent_palette["500"],
            accent_600=accent_palette["600"],
            accent_700=accent_palette["700"],
            accent_800=accent_palette["800"],
            accent_900=accent_palette["900"],

            # Luxury semantic colors
            success="#2d5a27",  # Forest green
            success_light="#90ee90",
            success_dark="#1a331a",

            warning="#b8860b",  # Dark goldenrod
            warning_light="#ffffe0",
            warning_dark="#8b6914",

            error="#8b0000",  # Dark red
            error_light="#ffb6c1",
            error_dark="#654321",

            info="#4682b4",  # Steel blue
            info_light="#e6f3ff",
            info_dark="#2f4f4f",

            # Luxury neutrals
            neutral_0="#ffffff" if mode == ThemeMode.LIGHT else "#0a0a0a",
            neutral_50="#fafafa" if mode == ThemeMode.LIGHT else "#1a1a1a",
            neutral_100="#f5f5f5" if mode == ThemeMode.LIGHT else "#262626",
            neutral_200="#e5e5e5" if mode == ThemeMode.LIGHT else "#404040",
            neutral_300="#d4d4d4" if mode == ThemeMode.LIGHT else "#525252",
            neutral_400="#a3a3a3",
            neutral_500="#737373",
            neutral_600="#525252" if mode == ThemeMode.LIGHT else "#d4d4d4",
            neutral_700="#404040" if mode == ThemeMode.LIGHT else "#e5e5e5",
            neutral_800="#262626" if mode == ThemeMode.LIGHT else "#f5f5f5",
            neutral_900="#171717" if mode == ThemeMode.LIGHT else "#fafafa",
            neutral_950="#0a0a0a" if mode == ThemeMode.LIGHT else "#ffffff",
        )

        # Luxury typography with serif accents
        typography = TypographyScale(
            font_family_primary='"Playfair Display", "Times New Roman", serif',
            font_family_secondary='"Montserrat", "SF Pro Display", sans-serif',
            font_family_mono='"JetBrains Mono", monospace',

            text_xs="0.75rem",
            text_sm="0.875rem",
            text_base="1rem",
            text_lg="1.125rem",
            text_xl="1.25rem",
            text_2xl="1.5rem",
            text_3xl="1.875rem",
            text_4xl="2.25rem",
            text_5xl="3rem",
            text_6xl="3.75rem",

            font_weight_thin="100",
            font_weight_extralight="200",
            font_weight_light="300",
            font_weight_normal="400",
            font_weight_medium="500",
            font_weight_semibold="600",
            font_weight_bold="700",
            font_weight_extrabold="800",
            font_weight_black="900",

            leading_none="1",
            leading_tight="1.25",
            leading_snug="1.375",
            leading_normal="1.5",
            leading_relaxed="1.625",
            leading_loose="2",

            tracking_tighter="-0.05em",
            tracking_tight="-0.025em",
            tracking_normal="0em",
            tracking_wide="0.025em",
            tracking_wider="0.05em",
            tracking_widest="0.1em",
        )

        # Use same spacing, border radius, shadows, and animations as professional theme
        spacing = SpacingScale(
            space_0="0px", space_px="1px", space_0_5="0.125rem", space_1="0.25rem",
            space_1_5="0.375rem", space_2="0.5rem", space_2_5="0.625rem", space_3="0.75rem",
            space_3_5="0.875rem", space_4="1rem", space_5="1.25rem", space_6="1.5rem",
            space_7="1.75rem", space_8="2rem", space_9="2.25rem", space_10="2.5rem",
            space_11="2.75rem", space_12="3rem", space_14="3.5rem", space_16="4rem",
            space_20="5rem", space_24="6rem", space_28="7rem", space_32="8rem",
            space_36="9rem", space_40="10rem", space_44="11rem", space_48="12rem",
            space_52="13rem", space_56="14rem", space_60="15rem", space_64="16rem",
            space_72="18rem", space_80="20rem", space_96="24rem"
        )

        border_radius = BorderRadiusScale(
            radius_none="0px", radius_sm="0.125rem", radius="0.25rem", radius_md="0.375rem",
            radius_lg="0.5rem", radius_xl="0.75rem", radius_2xl="1rem", radius_3xl="1.5rem",
            radius_full="9999px"
        )

        shadows = ShadowScale(
            shadow_none="0 0 #0000",
            shadow_sm="0 1px 2px 0 rgb(0 0 0 / 0.05)",
            shadow="0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)",
            shadow_md="0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
            shadow_lg="0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
            shadow_xl="0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
            shadow_2xl="0 25px 50px -12px rgb(0 0 0 / 0.25)",
            shadow_inner="inset 0 2px 4px 0 rgb(0 0 0 / 0.05)"
        )

        animations = AnimationScale(
            duration_75="75ms", duration_100="100ms", duration_150="150ms", duration_200="200ms",
            duration_300="300ms", duration_500="500ms", duration_700="700ms", duration_1000="1000ms",
            ease_linear="linear", ease_in="cubic-bezier(0.4, 0, 1, 1)",
            ease_out="cubic-bezier(0, 0, 0.2, 1)", ease_in_out="cubic-bezier(0.4, 0, 0.2, 1)"
        )

        theme = ThemeDefinition(
            name=f"Luxury Real Estate ({mode.value.title()})",
            category=ThemeCategory.LUXURY,
            mode=mode,
            description="Luxurious theme with gold accents and serif typography for high-end real estate applications.",
            colors=colors,
            typography=typography,
            spacing=spacing,
            border_radius=border_radius,
            shadows=shadows,
            animations=animations,
            tags=["luxury", "real_estate", "gold", "serif", "premium", "elegant"]
        )

        return theme

    def register_theme(self, theme: ThemeDefinition):
        """Register a theme in the factory."""
        self.themes[theme.name] = theme

    def get_theme(self, name: str) -> Optional[ThemeDefinition]:
        """Get a theme by name."""
        return self.themes.get(name)

    def list_themes(self) -> List[str]:
        """List all available theme names."""
        return list(self.themes.keys())

    def set_current_theme(self, theme: ThemeDefinition):
        """Set the current active theme."""
        self.current_theme = theme

    def save_theme(self, theme: ThemeDefinition, path: Path):
        """Save theme to JSON file."""
        with open(path, 'w') as f:
            f.write(theme.to_json())

    def load_theme(self, path: Path) -> ThemeDefinition:
        """Load theme from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return ThemeDefinition.from_dict(data)


class StreamlitThemeInjector:
    """Injects themes into Streamlit applications."""

    def __init__(self, theme: ThemeDefinition):
        self.theme = theme

    def inject_theme(self):
        """Inject the complete theme into Streamlit."""
        css = self._generate_complete_css()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

    def _generate_complete_css(self) -> str:
        """Generate complete CSS from theme definition."""
        css = f"""
        :root {{
            /* Color Tokens */
            --color-primary-50: {self.theme.colors.primary_50};
            --color-primary-100: {self.theme.colors.primary_100};
            --color-primary-200: {self.theme.colors.primary_200};
            --color-primary-300: {self.theme.colors.primary_300};
            --color-primary-400: {self.theme.colors.primary_400};
            --color-primary-500: {self.theme.colors.primary_500};
            --color-primary-600: {self.theme.colors.primary_600};
            --color-primary-700: {self.theme.colors.primary_700};
            --color-primary-800: {self.theme.colors.primary_800};
            --color-primary-900: {self.theme.colors.primary_900};

            --color-secondary-50: {self.theme.colors.secondary_50};
            --color-secondary-100: {self.theme.colors.secondary_100};
            --color-secondary-200: {self.theme.colors.secondary_200};
            --color-secondary-300: {self.theme.colors.secondary_300};
            --color-secondary-400: {self.theme.colors.secondary_400};
            --color-secondary-500: {self.theme.colors.secondary_500};
            --color-secondary-600: {self.theme.colors.secondary_600};
            --color-secondary-700: {self.theme.colors.secondary_700};
            --color-secondary-800: {self.theme.colors.secondary_800};
            --color-secondary-900: {self.theme.colors.secondary_900};

            --color-accent-50: {self.theme.colors.accent_50};
            --color-accent-100: {self.theme.colors.accent_100};
            --color-accent-200: {self.theme.colors.accent_200};
            --color-accent-300: {self.theme.colors.accent_300};
            --color-accent-400: {self.theme.colors.accent_400};
            --color-accent-500: {self.theme.colors.accent_500};
            --color-accent-600: {self.theme.colors.accent_600};
            --color-accent-700: {self.theme.colors.accent_700};
            --color-accent-800: {self.theme.colors.accent_800};
            --color-accent-900: {self.theme.colors.accent_900};

            --color-success: {self.theme.colors.success};
            --color-success-light: {self.theme.colors.success_light};
            --color-success-dark: {self.theme.colors.success_dark};

            --color-warning: {self.theme.colors.warning};
            --color-warning-light: {self.theme.colors.warning_light};
            --color-warning-dark: {self.theme.colors.warning_dark};

            --color-error: {self.theme.colors.error};
            --color-error-light: {self.theme.colors.error_light};
            --color-error-dark: {self.theme.colors.error_dark};

            --color-info: {self.theme.colors.info};
            --color-info-light: {self.theme.colors.info_light};
            --color-info-dark: {self.theme.colors.info_dark};

            --color-neutral-0: {self.theme.colors.neutral_0};
            --color-neutral-50: {self.theme.colors.neutral_50};
            --color-neutral-100: {self.theme.colors.neutral_100};
            --color-neutral-200: {self.theme.colors.neutral_200};
            --color-neutral-300: {self.theme.colors.neutral_300};
            --color-neutral-400: {self.theme.colors.neutral_400};
            --color-neutral-500: {self.theme.colors.neutral_500};
            --color-neutral-600: {self.theme.colors.neutral_600};
            --color-neutral-700: {self.theme.colors.neutral_700};
            --color-neutral-800: {self.theme.colors.neutral_800};
            --color-neutral-900: {self.theme.colors.neutral_900};
            --color-neutral-950: {self.theme.colors.neutral_950};

            /* Typography */
            --font-family-primary: {self.theme.typography.font_family_primary};
            --font-family-secondary: {self.theme.typography.font_family_secondary};
            --font-family-mono: {self.theme.typography.font_family_mono};

            --text-xs: {self.theme.typography.text_xs};
            --text-sm: {self.theme.typography.text_sm};
            --text-base: {self.theme.typography.text_base};
            --text-lg: {self.theme.typography.text_lg};
            --text-xl: {self.theme.typography.text_xl};
            --text-2xl: {self.theme.typography.text_2xl};
            --text-3xl: {self.theme.typography.text_3xl};
            --text-4xl: {self.theme.typography.text_4xl};
            --text-5xl: {self.theme.typography.text_5xl};
            --text-6xl: {self.theme.typography.text_6xl};

            --font-weight-thin: {self.theme.typography.font_weight_thin};
            --font-weight-extralight: {self.theme.typography.font_weight_extralight};
            --font-weight-light: {self.theme.typography.font_weight_light};
            --font-weight-normal: {self.theme.typography.font_weight_normal};
            --font-weight-medium: {self.theme.typography.font_weight_medium};
            --font-weight-semibold: {self.theme.typography.font_weight_semibold};
            --font-weight-bold: {self.theme.typography.font_weight_bold};
            --font-weight-extrabold: {self.theme.typography.font_weight_extrabold};
            --font-weight-black: {self.theme.typography.font_weight_black};

            /* Spacing */
            --space-0: {self.theme.spacing.space_0};
            --space-px: {self.theme.spacing.space_px};
            --space-0-5: {self.theme.spacing.space_0_5};
            --space-1: {self.theme.spacing.space_1};
            --space-1-5: {self.theme.spacing.space_1_5};
            --space-2: {self.theme.spacing.space_2};
            --space-3: {self.theme.spacing.space_3};
            --space-4: {self.theme.spacing.space_4};
            --space-5: {self.theme.spacing.space_5};
            --space-6: {self.theme.spacing.space_6};
            --space-8: {self.theme.spacing.space_8};
            --space-10: {self.theme.spacing.space_10};
            --space-12: {self.theme.spacing.space_12};
            --space-16: {self.theme.spacing.space_16};
            --space-20: {self.theme.spacing.space_20};
            --space-24: {self.theme.spacing.space_24};
            --space-32: {self.theme.spacing.space_32};

            /* Border Radius */
            --radius-none: {self.theme.border_radius.radius_none};
            --radius-sm: {self.theme.border_radius.radius_sm};
            --radius: {self.theme.border_radius.radius};
            --radius-md: {self.theme.border_radius.radius_md};
            --radius-lg: {self.theme.border_radius.radius_lg};
            --radius-xl: {self.theme.border_radius.radius_xl};
            --radius-2xl: {self.theme.border_radius.radius_2xl};
            --radius-3xl: {self.theme.border_radius.radius_3xl};
            --radius-full: {self.theme.border_radius.radius_full};

            /* Shadows */
            --shadow-none: {self.theme.shadows.shadow_none};
            --shadow-sm: {self.theme.shadows.shadow_sm};
            --shadow: {self.theme.shadows.shadow};
            --shadow-md: {self.theme.shadows.shadow_md};
            --shadow-lg: {self.theme.shadows.shadow_lg};
            --shadow-xl: {self.theme.shadows.shadow_xl};
            --shadow-2xl: {self.theme.shadows.shadow_2xl};
            --shadow-inner: {self.theme.shadows.shadow_inner};

            /* Animations */
            --duration-75: {self.theme.animations.duration_75};
            --duration-100: {self.theme.animations.duration_100};
            --duration-150: {self.theme.animations.duration_150};
            --duration-200: {self.theme.animations.duration_200};
            --duration-300: {self.theme.animations.duration_300};
            --duration-500: {self.theme.animations.duration_500};

            --ease-linear: {self.theme.animations.ease_linear};
            --ease-in: {self.theme.animations.ease_in};
            --ease-out: {self.theme.animations.ease_out};
            --ease-in-out: {self.theme.animations.ease_in_out};
        }}

        /* Global Application Styles */
        .stApp {{
            font-family: var(--font-family-primary);
            background-color: var(--color-neutral-0);
            color: var(--color-neutral-900);
        }}

        /* Main Content Area */
        .main .block-container {{
            background-color: var(--color-neutral-0);
            padding: var(--space-6) var(--space-4);
        }}

        /* Headers */
        h1 {{
            font-family: var(--font-family-primary);
            font-size: var(--text-4xl);
            font-weight: var(--font-weight-bold);
            color: var(--color-primary-700);
            margin-bottom: var(--space-6);
        }}

        h2 {{
            font-family: var(--font-family-primary);
            font-size: var(--text-3xl);
            font-weight: var(--font-weight-semibold);
            color: var(--color-primary-600);
            margin-bottom: var(--space-4);
        }}

        h3 {{
            font-family: var(--font-family-primary);
            font-size: var(--text-2xl);
            font-weight: var(--font-weight-semibold);
            color: var(--color-primary-600);
            margin-bottom: var(--space-3);
        }}

        /* Buttons */
        .stButton > button {{
            background: var(--color-primary-500);
            color: var(--color-neutral-0);
            border: none;
            border-radius: var(--radius-md);
            padding: var(--space-3) var(--space-6);
            font-family: var(--font-family-secondary);
            font-weight: var(--font-weight-medium);
            transition: all var(--duration-200) var(--ease-out);
            box-shadow: var(--shadow-sm);
        }}

        .stButton > button:hover {{
            background: var(--color-primary-600);
            box-shadow: var(--shadow-md);
            transform: translateY(-1px);
        }}

        .stButton > button:active {{
            transform: translateY(0);
            box-shadow: var(--shadow-sm);
        }}

        /* Form Elements */
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stSelectbox > div > div,
        .stNumberInput > div > div > input {{
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-md);
            font-family: var(--font-family-secondary);
            color: var(--color-neutral-700);
            background-color: var(--color-neutral-0);
            transition: border-color var(--duration-200) var(--ease-out);
        }}

        .stTextInput > div > div > input:focus,
        .stTextArea > div > div > textarea:focus,
        .stSelectbox > div > div:focus-within,
        .stNumberInput > div > div > input:focus {{
            border-color: var(--color-primary-400);
            box-shadow: 0 0 0 3px rgba({self.theme.colors.primary_200.replace('#', '')}, 0.1);
            outline: none;
        }}

        /* Sidebar */
        .css-1d391kg {{
            background-color: var(--color-neutral-50);
            border-right: 1px solid var(--color-neutral-200);
        }}

        /* Metrics */
        .metric-container {{
            background: var(--color-neutral-0);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            box-shadow: var(--shadow-sm);
        }}

        /* Cards */
        .element-container .stMarkdown {{
            background: var(--color-neutral-0);
        }}

        /* Status indicators */
        .status-success {{
            color: var(--color-success);
            background-color: var(--color-success-light);
            border: 1px solid var(--color-success);
            border-radius: var(--radius-sm);
            padding: var(--space-1) var(--space-2);
        }}

        .status-warning {{
            color: var(--color-warning);
            background-color: var(--color-warning-light);
            border: 1px solid var(--color-warning);
            border-radius: var(--radius-sm);
            padding: var(--space-1) var(--space-2);
        }}

        .status-error {{
            color: var(--color-error);
            background-color: var(--color-error-light);
            border: 1px solid var(--color-error);
            border-radius: var(--radius-sm);
            padding: var(--space-1) var(--space-2);
        }}

        /* Data tables */
        .stDataFrame {{
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-lg);
            overflow: hidden;
        }}

        /* Progress bars */
        .stProgress > div > div > div {{
            background: var(--color-primary-500);
            border-radius: var(--radius-full);
        }}

        /* Expanders */
        .streamlit-expanderHeader {{
            background: var(--color-neutral-50);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-md);
            color: var(--color-primary-700);
            font-weight: var(--font-weight-medium);
        }}

        /* Columns */
        .element-container {{
            gap: var(--space-4);
        }}

        /* Custom utility classes */
        .theme-card {{
            background: var(--color-neutral-0);
            border: 1px solid var(--color-neutral-200);
            border-radius: var(--radius-lg);
            padding: var(--space-6);
            box-shadow: var(--shadow-sm);
            transition: box-shadow var(--duration-200) var(--ease-out);
        }}

        .theme-card:hover {{
            box-shadow: var(--shadow-md);
        }}

        .theme-title {{
            font-size: var(--text-2xl);
            font-weight: var(--font-weight-bold);
            color: var(--color-primary-700);
            margin-bottom: var(--space-3);
        }}

        .theme-subtitle {{
            font-size: var(--text-lg);
            font-weight: var(--font-weight-semibold);
            color: var(--color-primary-600);
            margin-bottom: var(--space-2);
        }}

        .theme-text {{
            font-size: var(--text-base);
            color: var(--color-neutral-700);
            line-height: var(--leading-relaxed);
        }}

        .theme-text-muted {{
            font-size: var(--text-sm);
            color: var(--color-neutral-500);
            font-style: italic;
        }}
        """

        return css

    def inject_component_styles(self, component_overrides: Dict[str, str] = None):
        """Inject specific component style overrides."""
        if not component_overrides:
            return

        css = ""
        for selector, styles in component_overrides.items():
            css += f"{selector} {{ {styles} }}"

        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# Usage examples and theme presets
def create_enterprise_hub_themes():
    """Create themes specifically for EnterpriseHub GHL Real Estate AI."""

    factory = ThemeFactory()

    # Professional Real Estate Theme (Light)
    professional_light = factory.create_real_estate_theme(
        primary_color="#1e40af",  # Professional blue
        mode=ThemeMode.LIGHT
    )
    factory.register_theme(professional_light)

    # Professional Real Estate Theme (Dark)
    professional_dark = factory.create_real_estate_theme(
        primary_color="#1e40af",
        mode=ThemeMode.DARK
    )
    factory.register_theme(professional_dark)

    # Luxury Real Estate Theme (Light)
    luxury_light = factory.create_luxury_real_estate_theme(mode=ThemeMode.LIGHT)
    factory.register_theme(luxury_light)

    # Luxury Real Estate Theme (Dark)
    luxury_dark = factory.create_luxury_real_estate_theme(mode=ThemeMode.DARK)
    factory.register_theme(luxury_dark)

    return factory

def apply_theme_to_streamlit_app(theme_name: str = "Real Estate Professional (Light)"):
    """Apply a theme to the current Streamlit app."""
    factory = create_enterprise_hub_themes()
    theme = factory.get_theme(theme_name)

    if theme:
        injector = StreamlitThemeInjector(theme)
        injector.inject_theme()

        # Store theme in session state for component access
        st.session_state['current_theme'] = theme

        return theme
    else:
        st.error(f"Theme '{theme_name}' not found")
        return None

def create_theme_selector():
    """Create a theme selector widget for Streamlit apps."""
    factory = create_enterprise_hub_themes()
    theme_names = factory.list_themes()

    selected_theme = st.sidebar.selectbox(
        "Choose Theme",
        theme_names,
        index=0 if theme_names else 0
    )

    if selected_theme:
        theme = apply_theme_to_streamlit_app(selected_theme)
        if theme:
            st.sidebar.success(f"Applied theme: {selected_theme}")

            # Show theme preview
            with st.sidebar.expander("Theme Preview"):
                st.markdown(f"**Category:** {theme.category.value}")
                st.markdown(f"**Mode:** {theme.mode.value}")
                st.markdown(f"**Description:** {theme.description}")

                # Color preview
                st.markdown("**Colors:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f'<div style="background: {theme.colors.primary_500}; height: 20px; border-radius: 4px;"></div>', unsafe_allow_html=True)
                    st.markdown("Primary")
                with col2:
                    st.markdown(f'<div style="background: {theme.colors.secondary_500}; height: 20px; border-radius: 4px;"></div>', unsafe_allow_html=True)
                    st.markdown("Secondary")

    return selected_theme
```

## Best Practices

1. **Design Token Consistency**: Use design tokens for all styling decisions
2. **Accessibility**: Ensure sufficient color contrast and readable typography
3. **Brand Alignment**: Customize themes to match client brand guidelines
4. **Performance**: Minimize CSS complexity and reuse design tokens
5. **Maintainability**: Keep themes modular and well-documented
6. **Responsive Design**: Test themes across different screen sizes
7. **Theme Testing**: Test all themes with actual content and components

This theme factory skill provides a comprehensive system for creating professional, brand-consistent themes specifically tailored for the EnterpriseHub GHL Real Estate AI project, with support for both light and dark modes and industry-specific styling.
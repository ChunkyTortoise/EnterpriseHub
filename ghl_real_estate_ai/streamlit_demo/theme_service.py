"""
Obsidian Theme Service - Design Token System
Provides type-safe access to design tokens for consistent theming.
"""

from typing import Any, Dict


class ObsidianThemeService:
    """
    Centralized theme service with design tokens.
    Provides consistent access to colors, typography, spacing, and shadows.
    """

    TOKENS: Dict[str, Any] = {
        "colors": {
            "brand": {
                "primary": "#6366F1",
                "primary-glow": "rgba(99, 102, 241, 0.4)",
                "secondary": "#8B5CF6",
            },
            "background": {
                "deep": "#05070A",
                "card": "#161B22",
                "elevated": "#1C2128",
                "glass": "rgba(13, 17, 23, 0.8)",
            },
            "text": {
                "primary": "#FFFFFF",
                "secondary": "#E6EDF3",
                "muted": "#8B949E",
                "accent": "#6366F1",
            },
            "status": {
                "hot": "#EF4444",
                "warm": "#F59E0B",
                "cold": "#3B82F6",
                "success": "#10B981",
                "warning": "#F59E0B",
                "error": "#EF4444",
            },
            "primary": {
                "indigo": "#6366F1",
                "purple": "#8B5CF6",
                "blue": "#3B82F6",
            },
        },
        "typography": {
            "family": {
                "heading": "Space Grotesk, sans-serif",
                "body": "Inter, sans-serif",
                "mono": "JetBrains Mono, monospace",
            },
            "weight": {
                "heading": 700,
                "body": 400,
                "emphasis": 600,
            },
            "size": {
                "xs": "0.75rem",
                "sm": "0.875rem",
                "base": "1rem",
                "lg": "1.125rem",
                "xl": "1.25rem",
                "2xl": "1.5rem",
                "3xl": "1.875rem",
            },
        },
        "spacing": {
            "xs": "0.5rem",
            "sm": "1rem",
            "md": "1.5rem",
            "lg": "2.5rem",
            "xl": "4rem",
        },
        "radius": {
            "sm": "8px",
            "md": "12px",
            "lg": "16px",
            "xl": "20px",
            "full": "9999px",
        },
        "shadow": {
            "obsidian": "0 8px 32px 0 rgba(0, 0, 0, 0.8)",
            "glow-indigo": "0 0 25px rgba(99, 102, 241, 0.3)",
            "glow-red": "0 0 25px rgba(239, 68, 68, 0.3)",
            "glow-amber": "0 0 25px rgba(245, 158, 11, 0.3)",
            "glow-blue": "0 0 25px rgba(59, 130, 246, 0.3)",
        },
        "animation": {
            "duration": {
                "fast": "0.2s",
                "normal": "0.4s",
                "slow": "0.6s",
            },
            "easing": {
                "ease-out": "cubic-bezier(0.4, 0, 0.2, 1)",
                "ease-in-out": "cubic-bezier(0.4, 0, 0.6, 1)",
            },
        },
    }

    @classmethod
    def get_token(cls, path: str) -> Any:
        """
        Access token by dot-notation path.

        Args:
            path: Dot-separated path to token (e.g., 'colors.brand.primary')

        Returns:
            Token value

        Example:
            >>> theme = ObsidianThemeService()
            >>> theme.get_token('colors.brand.primary')
            '#6366F1'
            >>> theme.get_token('typography.family.heading')
            'Space Grotesk, sans-serif'
        """
        keys = path.split(".")
        value = cls.TOKENS

        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None

        return value

    @classmethod
    def css_var(cls, path: str) -> str:
        """
        Get CSS variable name for token path.

        Args:
            path: Dot-separated path to token

        Returns:
            CSS variable reference

        Example:
            >>> theme = ObsidianThemeService()
            >>> theme.css_var('colors.brand.primary')
            'var(--colors-brand-primary)'
        """
        var_name = "--" + path.replace(".", "-")
        return f"var({var_name})"


# Convenience accessors for common tokens
class Colors:
    """Quick access to color tokens"""

    PRIMARY = ObsidianThemeService.TOKENS["colors"]["brand"]["primary"]
    SECONDARY = ObsidianThemeService.TOKENS["colors"]["brand"]["secondary"]
    BACKGROUND_DEEP = ObsidianThemeService.TOKENS["colors"]["background"]["deep"]
    BACKGROUND_CARD = ObsidianThemeService.TOKENS["colors"]["background"]["card"]
    TEXT_PRIMARY = ObsidianThemeService.TOKENS["colors"]["text"]["primary"]
    TEXT_SECONDARY = ObsidianThemeService.TOKENS["colors"]["text"]["secondary"]
    TEXT_MUTED = ObsidianThemeService.TOKENS["colors"]["text"]["muted"]
    HOT = ObsidianThemeService.TOKENS["colors"]["status"]["hot"]
    WARM = ObsidianThemeService.TOKENS["colors"]["status"]["warm"]
    COLD = ObsidianThemeService.TOKENS["colors"]["status"]["cold"]


class Typography:
    """Quick access to typography tokens"""

    HEADING_FAMILY = ObsidianThemeService.TOKENS["typography"]["family"]["heading"]
    BODY_FAMILY = ObsidianThemeService.TOKENS["typography"]["family"]["body"]
    MONO_FAMILY = ObsidianThemeService.TOKENS["typography"]["family"]["mono"]
    HEADING_WEIGHT = ObsidianThemeService.TOKENS["typography"]["weight"]["heading"]
    BODY_WEIGHT = ObsidianThemeService.TOKENS["typography"]["weight"]["body"]


class Spacing:
    """Quick access to spacing tokens"""

    XS = ObsidianThemeService.TOKENS["spacing"]["xs"]
    SM = ObsidianThemeService.TOKENS["spacing"]["sm"]
    MD = ObsidianThemeService.TOKENS["spacing"]["md"]
    LG = ObsidianThemeService.TOKENS["spacing"]["lg"]
    XL = ObsidianThemeService.TOKENS["spacing"]["xl"]


__all__ = ["ObsidianThemeService", "Colors", "Typography", "Spacing"]

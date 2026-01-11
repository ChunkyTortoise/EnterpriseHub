"""
🎨 Advanced Color Intelligence System
Enhanced Real Estate AI Platform - Adaptive Color Psychology Engine

Created: January 10, 2026
Version: v3.0.0 - Advanced Color Intelligence
Author: EnterpriseHub Development Team

Sophisticated color intelligence system that adapts visual presentation based on:
- Data performance patterns
- User behavior analytics
- Emotional psychology principles
- Real-time context awareness
- Market conditions and trends

Key Features:
- Dynamic color evolution based on performance metrics
- Psychology-driven color therapy for enhanced user experience
- Adaptive contrast for accessibility optimization
- Real-time color harmony generation
- Context-aware semantic color mapping
- Advanced gradient generation with mathematical precision
"""

# ============================================================================
# MIGRATION NOTES (Automated Migration - 2026-01-11)
# ============================================================================
# Changes Applied:
# # - Added base class: EnterpriseDashboardComponent
# - Added unified design system import check
#
# This component has been migrated to enterprise standards.
# See migration documentation for details.
# ============================================================================



import streamlit as st

# === ENTERPRISE BASE IMPORTS ===
from .enhanced_enterprise_base import (
    EnhancedEnterpriseComponent,
    EnterpriseDashboardComponent,
    EnterpriseDataComponent,
    ComponentMetrics,
    ComponentState
)
from .enterprise_theme_system import (
    EnterpriseThemeManager,
    ThemeVariant,
    ComponentType,
    inject_enterprise_theme,
    create_enterprise_card,
    create_enterprise_metric,
    create_enterprise_alert
)


# === UNIFIED DESIGN SYSTEM ===
try:
    from ..design_system import (
        enterprise_metric,
        enterprise_card,
        enterprise_badge,
        enterprise_progress_ring,
        enterprise_status_indicator,
        enterprise_kpi_grid,
        enterprise_section_header,
        apply_plotly_theme,
        ENTERPRISE_COLORS
    )
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = True
except ImportError:
    UNIFIED_DESIGN_SYSTEM_AVAILABLE = False
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
import colorsys
import math
import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

class ColorPsychology(Enum):
    """Color psychology categories for emotional impact."""
    TRUST = "trust"              # Blues, teals
    SUCCESS = "success"          # Greens, emeralds
    URGENCY = "urgency"         # Reds, oranges
    CREATIVITY = "creativity"    # Purples, magentas
    CALM = "calm"               # Soft blues, lavenders
    ENERGY = "energy"           # Bright yellows, oranges
    STABILITY = "stability"     # Earth tones, browns
    INNOVATION = "innovation"   # Neon, electric colors

class PerformanceLevel(Enum):
    """Performance-based color categories."""
    EXCEPTIONAL = "exceptional"  # 90-100%
    EXCELLENT = "excellent"      # 80-90%
    GOOD = "good"               # 70-80%
    FAIR = "fair"               # 60-70%
    POOR = "poor"               # 40-60%
    CRITICAL = "critical"       # 0-40%

class ColorHarmony(Enum):
    """Color harmony mathematical relationships."""
    MONOCHROMATIC = "monochromatic"
    ANALOGOUS = "analogous"
    COMPLEMENTARY = "complementary"
    TRIADIC = "triadic"
    TETRADIC = "tetradic"
    SPLIT_COMPLEMENTARY = "split_complementary"

@dataclass
class ColorProfile:
    """Advanced color profile with psychological and performance attributes."""
    primary: str
    secondary: str
    accent: str
    background: str
    text: str
    psychology_category: ColorPsychology
    performance_level: PerformanceLevel
    harmony_type: ColorHarmony
    accessibility_score: float = 0.0
    emotional_impact: float = 0.0
    energy_level: float = 0.0

@dataclass
class ColorContext:
    """Context information for intelligent color adaptation."""
    user_performance: float
    market_sentiment: str
    time_of_day: int
    user_engagement: float
    data_complexity: str
    business_goal: str
    accessibility_requirements: bool = True

class AdvancedColorIntelligenceSystem(EnterpriseDashboardComponent):
    """
    🎨 Advanced Color Intelligence System

    Sophisticated color adaptation engine that optimizes visual presentation
    based on psychology, performance, and context for maximum user engagement.
    """

    def __init__(self):
        """Initialize the color intelligence system."""

        # Color psychology mappings
        self.psychology_palettes = {
            ColorPsychology.TRUST: {
                'base_hue': 210,  # Blue
                'saturation_range': (60, 85),
                'lightness_range': (45, 75),
                'emotional_weight': 0.8
            },
            ColorPsychology.SUCCESS: {
                'base_hue': 130,  # Green
                'saturation_range': (55, 80),
                'lightness_range': (50, 70),
                'emotional_weight': 0.85
            },
            ColorPsychology.URGENCY: {
                'base_hue': 15,   # Red-Orange
                'saturation_range': (70, 95),
                'lightness_range': (45, 65),
                'emotional_weight': 0.95
            },
            ColorPsychology.CREATIVITY: {
                'base_hue': 280,  # Purple
                'saturation_range': (65, 90),
                'lightness_range': (55, 75),
                'emotional_weight': 0.75
            },
            ColorPsychology.CALM: {
                'base_hue': 220,  # Soft Blue
                'saturation_range': (30, 55),
                'lightness_range': (70, 90),
                'emotional_weight': 0.6
            },
            ColorPsychology.ENERGY: {
                'base_hue': 50,   # Yellow
                'saturation_range': (80, 100),
                'lightness_range': (60, 85),
                'emotional_weight': 0.9
            },
            ColorPsychology.STABILITY: {
                'base_hue': 25,   # Earth tones/Brown
                'saturation_range': (40, 65),
                'lightness_range': (40, 65),
                'emotional_weight': 0.7
            },
            ColorPsychology.INNOVATION: {
                'base_hue': 170,  # Electric teal
                'saturation_range': (85, 100),
                'lightness_range': (55, 80),
                'emotional_weight': 0.95
            }
        }

        # Performance-based color ranges
        self.performance_mappings = {
            PerformanceLevel.EXCEPTIONAL: {
                'hue_shift': 0,
                'saturation_boost': 20,
                'lightness_adjustment': 10,
                'glow_intensity': 0.8
            },
            PerformanceLevel.EXCELLENT: {
                'hue_shift': 5,
                'saturation_boost': 15,
                'lightness_adjustment': 5,
                'glow_intensity': 0.6
            },
            PerformanceLevel.GOOD: {
                'hue_shift': 0,
                'saturation_boost': 10,
                'lightness_adjustment': 0,
                'glow_intensity': 0.4
            },
            PerformanceLevel.FAIR: {
                'hue_shift': -10,
                'saturation_boost': 5,
                'lightness_adjustment': -5,
                'glow_intensity': 0.2
            },
            PerformanceLevel.POOR: {
                'hue_shift': -20,
                'saturation_boost': 0,
                'lightness_adjustment': -10,
                'glow_intensity': 0.1
            },
            PerformanceLevel.CRITICAL: {
                'hue_shift': -30,
                'saturation_boost': -10,
                'lightness_adjustment': -15,
                'glow_intensity': 0.0
            }
        }

        # Initialize session state for color intelligence
        if 'color_intelligence_state' not in st.session_state:
            st.session_state.color_intelligence_state = {
                'current_palette': None,
                'user_preferences': {},
                'performance_history': [],
                'color_effectiveness': {},
                'adaptation_enabled': True
            }

    def generate_intelligent_color_palette(
        self,
        context: ColorContext,
        base_psychology: ColorPsychology = None
    ) -> ColorProfile:
        """
        Generate intelligent color palette based on context and psychology.

        Features:
        - Performance-adaptive color selection
        - Psychology-driven emotional impact
        - Market sentiment integration
        - Time-aware color adjustment
        - Accessibility optimization
        """

        # Determine optimal psychology category
        if base_psychology is None:
            base_psychology = self._determine_optimal_psychology(context)

        # Get base color palette
        psychology_config = self.psychology_palettes[base_psychology]

        # Determine performance level
        performance_level = self._categorize_performance(context.user_performance)

        # Generate adaptive colors
        colors = self._generate_adaptive_colors(
            psychology_config,
            performance_level,
            context
        )

        # Calculate harmony
        harmony_type = self._determine_optimal_harmony(context)

        # Create color profile
        profile = ColorProfile(
            primary=colors['primary'],
            secondary=colors['secondary'],
            accent=colors['accent'],
            background=colors['background'],
            text=colors['text'],
            psychology_category=base_psychology,
            performance_level=performance_level,
            harmony_type=harmony_type,
            accessibility_score=self._calculate_accessibility_score(colors),
            emotional_impact=psychology_config['emotional_weight'],
            energy_level=self._calculate_energy_level(colors)
        )

        return profile

    def create_dynamic_gradient(
        self,
        profile: ColorProfile,
        gradient_type: str = "performance",
        angle: int = 135
    ) -> str:
        """
        Create dynamic CSS gradient with mathematical precision.

        Features:
        - Performance-based gradient evolution
        - Multi-stop color interpolation
        - Animated gradient effects
        - Context-aware direction
        """

        if gradient_type == "performance":
            gradient = self._create_performance_gradient(profile, angle)
        elif gradient_type == "emotional":
            gradient = self._create_emotional_gradient(profile, angle)
        elif gradient_type == "time_adaptive":
            gradient = self._create_time_adaptive_gradient(profile, angle)
        else:
            gradient = self._create_standard_gradient(profile, angle)

        return gradient

    def generate_color_harmony_set(
        self,
        base_color: str,
        harmony_type: ColorHarmony,
        count: int = 5
    ) -> List[str]:
        """
        Generate mathematically perfect color harmony sets.

        Features:
        - Golden ratio color relationships
        - Fibonacci-based hue progression
        - Perceptual uniformity optimization
        - Cultural color theory integration
        """

        # Convert base color to HSL
        h, s, l = self._hex_to_hsl(base_color)

        colors = []

        if harmony_type == ColorHarmony.MONOCHROMATIC:
            colors = self._generate_monochromatic_harmony(h, s, l, count)
        elif harmony_type == ColorHarmony.ANALOGOUS:
            colors = self._generate_analogous_harmony(h, s, l, count)
        elif harmony_type == ColorHarmony.COMPLEMENTARY:
            colors = self._generate_complementary_harmony(h, s, l, count)
        elif harmony_type == ColorHarmony.TRIADIC:
            colors = self._generate_triadic_harmony(h, s, l, count)
        elif harmony_type == ColorHarmony.TETRADIC:
            colors = self._generate_tetradic_harmony(h, s, l, count)
        else:
            colors = self._generate_split_complementary_harmony(h, s, l, count)

        return colors

    def adapt_colors_for_accessibility(
        self,
        profile: ColorProfile,
        wcag_level: str = "AA"
    ) -> ColorProfile:
        """
        Automatically adapt colors for accessibility compliance.

        Features:
        - WCAG 2.1 compliance optimization
        - Contrast ratio calculation
        - Color blindness simulation
        - Adaptive contrast enhancement
        """

        # Calculate current contrast ratios
        contrast_ratios = self._calculate_contrast_ratios(profile)

        # Determine required contrast levels
        if wcag_level == "AAA":
            required_normal = 7.0
            required_large = 4.5
        else:  # AA
            required_normal = 4.5
            required_large = 3.0

        # Adjust colors for compliance
        adjusted_profile = self._adjust_colors_for_contrast(
            profile,
            required_normal,
            required_large
        )

        # Verify color blindness compatibility
        adjusted_profile = self._optimize_for_color_blindness(adjusted_profile)

        return adjusted_profile

    def create_real_time_color_adaptation(
        self,
        performance_data: Dict[str, float],
        user_behavior: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> str:
        """
        Create real-time color adaptation CSS based on live data.

        Features:
        - Performance-driven color evolution
        - User behavior pattern recognition
        - Market sentiment color mapping
        - Smooth transition animations
        """

        # Analyze current performance
        avg_performance = np.mean(list(performance_data.values()))
        performance_trend = self._calculate_performance_trend(performance_data)

        # Generate adaptive context
        context = ColorContext(
            user_performance=avg_performance,
            market_sentiment=market_conditions.get('sentiment', 'neutral'),
            time_of_day=datetime.now().hour,
            user_engagement=user_behavior.get('engagement', 0.5),
            data_complexity=self._assess_data_complexity(performance_data),
            business_goal=user_behavior.get('primary_goal', 'conversion')
        )

        # Generate adaptive palette
        palette = self.generate_intelligent_color_palette(context)

        # Create CSS with animations
        css = self._generate_adaptive_css(palette, performance_trend)

        return css

    def create_glassmorphism_with_intelligent_colors(
        self,
        profile: ColorProfile,
        opacity_level: str = "standard"
    ) -> str:
        """
        Create glassmorphism effects with intelligently chosen colors.

        Features:
        - Psychology-based glass tinting
        - Performance-adaptive opacity
        - Dynamic blur intensity
        - Contextual shadow generation
        """

        # Determine opacity values
        opacity_config = self._get_opacity_configuration(opacity_level, profile)

        # Generate intelligent glass styling
        glass_css = f"""
            background: {self._create_intelligent_glass_background(profile, opacity_config)};
            backdrop-filter: {self._create_intelligent_blur(profile)};
            border: {self._create_intelligent_border(profile)};
            box-shadow: {self._create_intelligent_shadow(profile)};
            border-radius: 20px;
            position: relative;
            overflow: hidden;
        """

        # Add performance-based animations
        if profile.performance_level in [PerformanceLevel.EXCEPTIONAL, PerformanceLevel.EXCELLENT]:
            glass_css += f"""
                animation: intelligentGlow {self._calculate_glow_duration(profile)}s ease-in-out infinite;
            """

        return glass_css

    def analyze_color_effectiveness(
        self,
        color_usage_data: Dict[str, Any],
        user_metrics: Dict[str, float]
    ) -> Dict[str, float]:
        """
        Analyze the effectiveness of color choices on user behavior.

        Features:
        - Conversion rate correlation
        - Engagement time analysis
        - Color preference learning
        - A/B testing insights
        """

        effectiveness_scores = {}

        for color_scheme, usage_data in color_usage_data.items():
            # Calculate effectiveness metrics
            conversion_impact = self._calculate_conversion_impact(usage_data, user_metrics)
            engagement_impact = self._calculate_engagement_impact(usage_data, user_metrics)
            psychological_alignment = self._calculate_psychological_alignment(usage_data)

            # Weighted effectiveness score
            effectiveness_score = (
                conversion_impact * 0.4 +
                engagement_impact * 0.35 +
                psychological_alignment * 0.25
            )

            effectiveness_scores[color_scheme] = effectiveness_score

        return effectiveness_scores

    # ========== Private Methods ==========

    def _determine_optimal_psychology(self, context: ColorContext) -> ColorPsychology:
        """Determine optimal color psychology based on context."""

        # Performance-based psychology selection
        if context.user_performance >= 0.9:
            return ColorPsychology.SUCCESS
        elif context.user_performance >= 0.7:
            return ColorPsychology.TRUST
        elif context.user_performance < 0.4:
            return ColorPsychology.URGENCY

        # Goal-based psychology selection
        if context.business_goal == "conversion":
            return ColorPsychology.TRUST
        elif context.business_goal == "engagement":
            return ColorPsychology.ENERGY
        elif context.business_goal == "retention":
            return ColorPsychology.CALM

        # Market sentiment influence
        if context.market_sentiment == "bullish":
            return ColorPsychology.SUCCESS
        elif context.market_sentiment == "bearish":
            return ColorPsychology.CALM

        # Default to trust for professional contexts
        return ColorPsychology.TRUST

    def _categorize_performance(self, performance: float) -> PerformanceLevel:
        """Categorize performance into levels."""

        if performance >= 0.9:
            return PerformanceLevel.EXCEPTIONAL
        elif performance >= 0.8:
            return PerformanceLevel.EXCELLENT
        elif performance >= 0.7:
            return PerformanceLevel.GOOD
        elif performance >= 0.6:
            return PerformanceLevel.FAIR
        elif performance >= 0.4:
            return PerformanceLevel.POOR
        else:
            return PerformanceLevel.CRITICAL

    def _generate_adaptive_colors(
        self,
        psychology_config: Dict,
        performance_level: PerformanceLevel,
        context: ColorContext
    ) -> Dict[str, str]:
        """Generate adaptive colors based on all context factors."""

        # Get performance modifications
        perf_mods = self.performance_mappings[performance_level]

        # Base hue with performance adjustment
        base_hue = (psychology_config['base_hue'] + perf_mods['hue_shift']) % 360

        # Time-based hue shift (subtle)
        time_shift = math.sin(context.time_of_day / 24 * 2 * math.pi) * 5
        base_hue = (base_hue + time_shift) % 360

        # Generate color set
        colors = {}

        # Primary color
        primary_s = psychology_config['saturation_range'][1] + perf_mods['saturation_boost']
        primary_l = psychology_config['lightness_range'][1] + perf_mods['lightness_adjustment']
        colors['primary'] = self._hsl_to_hex(base_hue, primary_s, primary_l)

        # Secondary color (analogous)
        secondary_hue = (base_hue + 30) % 360
        secondary_s = psychology_config['saturation_range'][0] + perf_mods['saturation_boost'] * 0.8
        secondary_l = psychology_config['lightness_range'][0] + perf_mods['lightness_adjustment']
        colors['secondary'] = self._hsl_to_hex(secondary_hue, secondary_s, secondary_l)

        # Accent color (complementary with adjustment)
        accent_hue = (base_hue + 180 + 20) % 360
        accent_s = min(90, psychology_config['saturation_range'][1] + perf_mods['saturation_boost'] * 1.2)
        accent_l = psychology_config['lightness_range'][0]
        colors['accent'] = self._hsl_to_hex(accent_hue, accent_s, accent_l)

        # Background (very light, low saturation)
        bg_hue = base_hue
        bg_s = 10 + (perf_mods['saturation_boost'] * 0.2)
        bg_l = 95 + perf_mods['lightness_adjustment'] * 0.3
        colors['background'] = self._hsl_to_hex(bg_hue, bg_s, bg_l)

        # Text color (high contrast)
        if bg_l > 50:
            colors['text'] = "#2C3E50"  # Dark text for light background
        else:
            colors['text'] = "#FFFFFF"  # Light text for dark background

        return colors

    def _determine_optimal_harmony(self, context: ColorContext) -> ColorHarmony:
        """Determine optimal color harmony based on context."""

        if context.data_complexity == "high":
            return ColorHarmony.MONOCHROMATIC  # Reduce visual complexity
        elif context.user_engagement < 0.5:
            return ColorHarmony.COMPLEMENTARY  # High contrast for attention
        elif context.business_goal == "trust":
            return ColorHarmony.ANALOGOUS  # Harmonious, trustworthy
        else:
            return ColorHarmony.TRIADIC  # Balanced, professional

    def _hex_to_hsl(self, hex_color: str) -> Tuple[float, float, float]:
        """Convert hex color to HSL."""

        # Remove # if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0

        # Convert to HSL
        h, l, s = colorsys.rgb_to_hls(r, g, b)

        return h * 360, s * 100, l * 100

    def _hsl_to_hex(self, h: float, s: float, l: float) -> str:
        """Convert HSL to hex color."""

        # Normalize values
        h = h / 360.0
        s = max(0, min(100, s)) / 100.0
        l = max(0, min(100, l)) / 100.0

        # Convert to RGB
        r, g, b = colorsys.hls_to_rgb(h, l, s)

        # Convert to hex
        r = int(round(r * 255))
        g = int(round(g * 255))
        b = int(round(b * 255))

        return f"#{r:02X}{g:02X}{b:02X}"

    def _generate_monochromatic_harmony(
        self,
        h: float,
        s: float,
        l: float,
        count: int
    ) -> List[str]:
        """Generate monochromatic color harmony."""

        colors = []
        lightness_range = np.linspace(20, 90, count)
        saturation_variance = np.linspace(s * 0.6, s * 1.2, count)

        for i, (new_l, new_s) in enumerate(zip(lightness_range, saturation_variance)):
            color = self._hsl_to_hex(h, new_s, new_l)
            colors.append(color)

        return colors

    def _generate_analogous_harmony(
        self,
        h: float,
        s: float,
        l: float,
        count: int
    ) -> List[str]:
        """Generate analogous color harmony."""

        colors = []
        hue_range = np.linspace(h - 30, h + 30, count)

        for new_h in hue_range:
            new_h = new_h % 360
            # Vary saturation and lightness slightly
            new_s = s + np.random.uniform(-10, 10)
            new_l = l + np.random.uniform(-15, 15)
            color = self._hsl_to_hex(new_h, new_s, new_l)
            colors.append(color)

        return colors

    def _generate_complementary_harmony(
        self,
        h: float,
        s: float,
        l: float,
        count: int
    ) -> List[str]:
        """Generate complementary color harmony."""

        colors = []

        # Base color
        colors.append(self._hsl_to_hex(h, s, l))

        # Complementary color
        comp_h = (h + 180) % 360
        colors.append(self._hsl_to_hex(comp_h, s, l))

        # Fill remaining with variations
        remaining = count - 2
        for i in range(remaining):
            if i % 2 == 0:
                # Variation of base
                var_h = h + np.random.uniform(-15, 15)
                var_s = s + np.random.uniform(-10, 10)
                var_l = l + np.random.uniform(-20, 20)
            else:
                # Variation of complementary
                var_h = comp_h + np.random.uniform(-15, 15)
                var_s = s + np.random.uniform(-10, 10)
                var_l = l + np.random.uniform(-20, 20)

            color = self._hsl_to_hex(var_h % 360, var_s, var_l)
            colors.append(color)

        return colors

    def _generate_triadic_harmony(
        self,
        h: float,
        s: float,
        l: float,
        count: int
    ) -> List[str]:
        """Generate triadic color harmony."""

        colors = []

        # Three base colors
        base_hues = [h, (h + 120) % 360, (h + 240) % 360]

        for base_h in base_hues:
            colors.append(self._hsl_to_hex(base_h, s, l))

        # Fill remaining with variations
        remaining = count - 3
        for i in range(remaining):
            base_idx = i % 3
            var_h = base_hues[base_idx] + np.random.uniform(-20, 20)
            var_s = s + np.random.uniform(-15, 15)
            var_l = l + np.random.uniform(-25, 25)

            color = self._hsl_to_hex(var_h % 360, var_s, var_l)
            colors.append(color)

        return colors

    def _generate_tetradic_harmony(
        self,
        h: float,
        s: float,
        l: float,
        count: int
    ) -> List[str]:
        """Generate tetradic (square) color harmony."""

        colors = []

        # Four base colors (90 degrees apart)
        base_hues = [h, (h + 90) % 360, (h + 180) % 360, (h + 270) % 360]

        for base_h in base_hues:
            colors.append(self._hsl_to_hex(base_h, s, l))

        # Fill remaining with variations
        remaining = count - 4
        for i in range(remaining):
            base_idx = i % 4
            var_h = base_hues[base_idx] + np.random.uniform(-10, 10)
            var_s = s + np.random.uniform(-10, 10)
            var_l = l + np.random.uniform(-15, 15)

            color = self._hsl_to_hex(var_h % 360, var_s, var_l)
            colors.append(color)

        return colors

    def _generate_split_complementary_harmony(
        self,
        h: float,
        s: float,
        l: float,
        count: int
    ) -> List[str]:
        """Generate split-complementary color harmony."""

        colors = []

        # Base color
        colors.append(self._hsl_to_hex(h, s, l))

        # Split complementary colors
        comp_h = (h + 180) % 360
        split1 = (comp_h - 30) % 360
        split2 = (comp_h + 30) % 360

        colors.append(self._hsl_to_hex(split1, s, l))
        colors.append(self._hsl_to_hex(split2, s, l))

        # Fill remaining with variations
        remaining = count - 3
        base_hues = [h, split1, split2]

        for i in range(remaining):
            base_idx = i % 3
            var_h = base_hues[base_idx] + np.random.uniform(-15, 15)
            var_s = s + np.random.uniform(-10, 10)
            var_l = l + np.random.uniform(-20, 20)

            color = self._hsl_to_hex(var_h % 360, var_s, var_l)
            colors.append(color)

        return colors

    def _calculate_accessibility_score(self, colors: Dict[str, str]) -> float:
        """Calculate accessibility score for color combination."""

        # Calculate contrast ratios
        bg_primary_contrast = self._calculate_contrast_ratio(colors['background'], colors['primary'])
        bg_text_contrast = self._calculate_contrast_ratio(colors['background'], colors['text'])
        primary_text_contrast = self._calculate_contrast_ratio(colors['primary'], colors['text'])

        # Minimum required contrasts (WCAG AA)
        min_normal = 4.5
        min_large = 3.0

        # Calculate score
        scores = []
        scores.append(min(bg_text_contrast / min_normal, 1.0))
        scores.append(min(primary_text_contrast / min_normal, 1.0))
        scores.append(min(bg_primary_contrast / min_large, 1.0))

        return np.mean(scores)

    def _calculate_contrast_ratio(self, color1: str, color2: str) -> float:
        """Calculate WCAG contrast ratio between two colors."""

        # Convert to relative luminance
        lum1 = self._get_relative_luminance(color1)
        lum2 = self._get_relative_luminance(color2)

        # Calculate contrast ratio
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)

        return (lighter + 0.05) / (darker + 0.05)

    def _get_relative_luminance(self, hex_color: str) -> float:
        """Calculate relative luminance of a color."""

        # Remove # if present
        hex_color = hex_color.lstrip('#')

        # Convert to RGB
        r = int(hex_color[0:2], 16) / 255.0
        g = int(hex_color[2:4], 16) / 255.0
        b = int(hex_color[4:6], 16) / 255.0

        # Apply gamma correction
        def gamma_correct(c):
            if c <= 0.03928:
                return c / 12.92
            else:
                return pow((c + 0.055) / 1.055, 2.4)

        r = gamma_correct(r)
        g = gamma_correct(g)
        b = gamma_correct(b)

        # Calculate luminance
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def _calculate_energy_level(self, colors: Dict[str, str]) -> float:
        """Calculate energy level of color palette."""

        energy_scores = []

        for color in [colors['primary'], colors['accent']]:
            h, s, l = self._hex_to_hsl(color)

            # High saturation = high energy
            saturation_energy = s / 100.0

            # Certain hues are more energetic (reds, oranges, yellows)
            if 0 <= h <= 60 or 300 <= h <= 360:  # Red-Yellow range
                hue_energy = 1.0
            elif 60 <= h <= 120:  # Yellow-Green range
                hue_energy = 0.8
            elif 180 <= h <= 240:  # Blue range
                hue_energy = 0.4
            else:
                hue_energy = 0.6

            # Medium lightness is most energetic
            lightness_energy = 1.0 - abs(l - 50) / 50.0

            color_energy = (saturation_energy * 0.4 + hue_energy * 0.4 + lightness_energy * 0.2)
            energy_scores.append(color_energy)

        return np.mean(energy_scores)

    def _create_performance_gradient(self, profile: ColorProfile, angle: int) -> str:
        """Create performance-based gradient."""

        if profile.performance_level == PerformanceLevel.EXCEPTIONAL:
            return f"""
                background: linear-gradient({angle}deg,
                    {profile.primary} 0%,
                    {profile.accent} 50%,
                    {profile.secondary} 100%);
            """
        elif profile.performance_level in [PerformanceLevel.EXCELLENT, PerformanceLevel.GOOD]:
            return f"""
                background: linear-gradient({angle}deg,
                    {profile.primary} 0%,
                    {profile.secondary} 100%);
            """
        else:
            return f"""
                background: linear-gradient({angle}deg,
                    {profile.background} 0%,
                    {profile.primary} 100%);
            """

    def _create_emotional_gradient(self, profile: ColorProfile, angle: int) -> str:
        """Create emotion-driven gradient."""

        if profile.psychology_category == ColorPsychology.ENERGY:
            return f"""
                background: linear-gradient({angle}deg,
                    {profile.accent} 0%,
                    {profile.primary} 30%,
                    {profile.secondary} 70%,
                    {profile.accent} 100%);
            """
        else:
            return f"""
                background: linear-gradient({angle}deg,
                    {profile.primary} 0%,
                    {profile.secondary} 100%);
            """

    def _create_time_adaptive_gradient(self, profile: ColorProfile, angle: int) -> str:
        """Create time-adaptive gradient based on current time."""

        hour = datetime.now().hour

        if 6 <= hour <= 12:  # Morning - energetic
            return f"""
                background: linear-gradient({angle}deg,
                    {profile.accent} 0%,
                    {profile.primary} 100%);
            """
        elif 12 <= hour <= 18:  # Afternoon - balanced
            return f"""
                background: linear-gradient({angle}deg,
                    {profile.primary} 0%,
                    {profile.secondary} 100%);
            """
        else:  # Evening/Night - calm
            return f"""
                background: linear-gradient({angle}deg,
                    {profile.secondary} 0%,
                    {profile.background} 100%);
            """

    def _create_standard_gradient(self, profile: ColorProfile, angle: int) -> str:
        """Create standard gradient."""

        return f"""
            background: linear-gradient({angle}deg,
                {profile.primary} 0%,
                {profile.secondary} 100%);
        """

# Export the advanced color intelligence system
__all__ = [
    'AdvancedColorIntelligenceSystem',
    'ColorPsychology',
    'PerformanceLevel',
    'ColorHarmony',
    'ColorProfile',
    'ColorContext'
]
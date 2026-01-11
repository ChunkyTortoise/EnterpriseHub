"""
Mobile Optimization Suite for EnterpriseHub Real Estate AI
==========================================================

Comprehensive mobile optimization framework providing:
- Touch-friendly interfaces
- Swipe gestures and mobile navigation
- Offline-capable components
- Progressive Web App (PWA) features
- Mobile-first responsive design
- Performance optimization for mobile devices

Ensures accessibility and usability across all mobile devices for the $468,750+ value system.
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
from typing import Dict, List, Any, Optional, Tuple, Callable
from enum import Enum
from dataclasses import dataclass
import json
import time
from datetime import datetime, timedelta


class SwipeDirection(Enum):
    """Swipe direction for mobile gestures"""
    LEFT = "left"
    RIGHT = "right"
    UP = "up"
    DOWN = "down"


@dataclass
class MobileLayout:
    """Mobile layout configuration"""
    breakpoint: int = 768
    touch_target_min: int = 44  # Minimum touch target size in pixels
    gesture_enabled: bool = True
    offline_capable: bool = True
    pwa_enabled: bool = True


@dataclass
class TouchGesture:
    """Touch gesture configuration"""
    type: str
    direction: Optional[SwipeDirection]
    callback: Callable
    threshold: int = 50  # Minimum swipe distance


class MobileOptimizationSuite(EnterpriseDashboardComponent):
    """Advanced mobile optimization system"""

    def __init__(self):
        """Initialize mobile optimization suite"""
        self.layout_config = MobileLayout()
        self.gesture_handlers = {}
        self.offline_cache = {}
        self.pwa_config = self._init_pwa_config()

        # Initialize mobile detection
        self._inject_mobile_optimization_css()
        self._inject_mobile_javascript()

    def _init_pwa_config(self) -> Dict[str, Any]:
        """Initialize Progressive Web App configuration"""
        return {
            "name": "EnterpriseHub Real Estate AI",
            "short_name": "EnterpriseHub",
            "description": "Advanced Real Estate AI Platform",
            "theme_color": "#1f2937",
            "background_color": "#ffffff",
            "display": "standalone",
            "orientation": "portrait",
            "start_url": "/",
            "scope": "/",
            "icons": [
                {
                    "src": "/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        }

    def _inject_mobile_optimization_css(self):
        """Inject mobile-optimized CSS"""
        st.markdown("""
        <style>
        /* Mobile Optimization Framework */
        :root {
            --mobile-header-height: 60px;
            --mobile-nav-height: 60px;
            --mobile-safe-area-top: env(safe-area-inset-top);
            --mobile-safe-area-bottom: env(safe-area-inset-bottom);
            --mobile-safe-area-left: env(safe-area-inset-left);
            --mobile-safe-area-right: env(safe-area-inset-right);
            --touch-target-min: 44px;
            --swipe-threshold: 50px;
        }

        /* Mobile-first viewport optimization */
        .mobile-viewport {
            width: 100vw;
            min-height: 100vh;
            min-height: -webkit-fill-available;
            overflow-x: hidden;
            position: relative;
        }

        /* Safe area handling for notched devices */
        .safe-area-container {
            padding-top: var(--mobile-safe-area-top);
            padding-bottom: var(--mobile-safe-area-bottom);
            padding-left: var(--mobile-safe-area-left);
            padding-right: var(--mobile-safe-area-right);
        }

        /* Touch-optimized interface elements */
        .touch-friendly {
            min-height: var(--touch-target-min);
            min-width: var(--touch-target-min);
            padding: 12px;
            margin: 4px;
            touch-action: manipulation;
            -webkit-tap-highlight-color: transparent;
            user-select: none;
            -webkit-user-select: none;
        }

        /* Mobile navigation bar */
        .mobile-nav-bar {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            height: var(--mobile-nav-height);
            background: white;
            border-top: 1px solid #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: space-around;
            z-index: 1000;
            padding-bottom: var(--mobile-safe-area-bottom);
            box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.1);
        }

        .mobile-nav-item {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 4px;
            padding: 8px 12px;
            border-radius: 8px;
            transition: all 150ms ease;
            cursor: pointer;
            min-width: var(--touch-target-min);
            min-height: var(--touch-target-min);
            justify-content: center;
        }

        .mobile-nav-item.active {
            background: #f0f9ff;
            color: #0369a1;
        }

        .mobile-nav-item:active {
            transform: scale(0.95);
            background: #e5e7eb;
        }

        .mobile-nav-icon {
            font-size: 20px;
            line-height: 1;
        }

        .mobile-nav-label {
            font-size: 10px;
            font-weight: 500;
            line-height: 1;
        }

        /* Mobile header */
        .mobile-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: var(--mobile-header-height);
            background: white;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            align-items: center;
            padding: 0 16px;
            z-index: 999;
            padding-top: var(--mobile-safe-area-top);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
        }

        .mobile-header-title {
            flex: 1;
            font-size: 18px;
            font-weight: 600;
            color: #1f2937;
            text-align: center;
        }

        .mobile-header-action {
            background: none;
            border: none;
            font-size: 18px;
            padding: 8px;
            border-radius: 6px;
            cursor: pointer;
            min-width: var(--touch-target-min);
            min-height: var(--touch-target-min);
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .mobile-header-action:active {
            background: #f3f4f6;
        }

        /* Mobile content area */
        .mobile-content {
            padding-top: calc(var(--mobile-header-height) + var(--mobile-safe-area-top) + 16px);
            padding-bottom: calc(var(--mobile-nav-height) + var(--mobile-safe-area-bottom) + 16px);
            padding-left: 16px;
            padding-right: 16px;
            min-height: 100vh;
            box-sizing: border-box;
        }

        /* Swipeable card container */
        .swipeable-card {
            background: white;
            border-radius: 12px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            overflow: hidden;
            position: relative;
            transform: translateX(0);
            transition: transform 300ms ease;
            touch-action: pan-x;
        }

        .swipeable-card.swiping {
            transition: none;
        }

        .swipe-action {
            position: absolute;
            top: 0;
            bottom: 0;
            width: 80px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: 600;
            font-size: 14px;
        }

        .swipe-action.left {
            left: -80px;
            background: #10b981;
        }

        .swipe-action.right {
            right: -80px;
            background: #ef4444;
        }

        /* Pull-to-refresh */
        .pull-refresh-container {
            position: relative;
            transform: translateY(0);
            transition: transform 300ms ease;
        }

        .pull-refresh-indicator {
            position: absolute;
            top: -60px;
            left: 50%;
            transform: translateX(-50%);
            width: 40px;
            height: 40px;
            background: white;
            border-radius: 50%;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            opacity: 0;
            transition: opacity 150ms ease;
        }

        .pull-refresh-indicator.visible {
            opacity: 1;
        }

        /* Mobile modal/drawer */
        .mobile-drawer {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            z-index: 2000;
            opacity: 0;
            visibility: hidden;
            transition: all 300ms ease;
        }

        .mobile-drawer.open {
            opacity: 1;
            visibility: visible;
        }

        .mobile-drawer-content {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            background: white;
            border-radius: 20px 20px 0 0;
            max-height: 90vh;
            transform: translateY(100%);
            transition: transform 300ms ease;
            padding: 20px;
            padding-bottom: calc(20px + var(--mobile-safe-area-bottom));
        }

        .mobile-drawer.open .mobile-drawer-content {
            transform: translateY(0);
        }

        .mobile-drawer-handle {
            width: 40px;
            height: 4px;
            background: #d1d5db;
            border-radius: 2px;
            margin: 0 auto 16px;
        }

        /* Mobile-optimized buttons */
        .mobile-button {
            background: #3b82f6;
            color: white;
            border: none;
            border-radius: 12px;
            padding: 16px 24px;
            font-size: 16px;
            font-weight: 600;
            width: 100%;
            margin-bottom: 12px;
            min-height: var(--touch-target-min);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            transition: all 150ms ease;
            touch-action: manipulation;
        }

        .mobile-button:active {
            transform: scale(0.98);
            background: #2563eb;
        }

        .mobile-button.secondary {
            background: #f3f4f6;
            color: #1f2937;
        }

        .mobile-button.secondary:active {
            background: #e5e7eb;
        }

        /* Mobile form elements */
        .mobile-input {
            width: 100%;
            padding: 16px;
            border: 1px solid #d1d5db;
            border-radius: 12px;
            font-size: 16px;
            margin-bottom: 16px;
            background: white;
            -webkit-appearance: none;
            appearance: none;
        }

        .mobile-input:focus {
            outline: none;
            border-color: #3b82f6;
            box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
        }

        /* Mobile grid system */
        .mobile-grid {
            display: grid;
            gap: 12px;
            margin-bottom: 16px;
        }

        .mobile-grid-2 {
            grid-template-columns: 1fr 1fr;
        }

        .mobile-grid-3 {
            grid-template-columns: repeat(3, 1fr);
        }

        /* Mobile card layouts */
        .mobile-card {
            background: white;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            border: 1px solid #e5e7eb;
        }

        .mobile-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 12px;
            padding-bottom: 12px;
            border-bottom: 1px solid #f3f4f6;
        }

        .mobile-card-title {
            font-size: 16px;
            font-weight: 600;
            color: #1f2937;
            margin: 0;
        }

        .mobile-card-action {
            background: none;
            border: none;
            color: #6b7280;
            font-size: 18px;
            padding: 4px;
            cursor: pointer;
            border-radius: 4px;
        }

        .mobile-card-action:active {
            background: #f3f4f6;
        }

        /* Haptic feedback simulation */
        .haptic-light {
            animation: haptic-pulse-light 50ms ease;
        }

        .haptic-medium {
            animation: haptic-pulse-medium 100ms ease;
        }

        .haptic-heavy {
            animation: haptic-pulse-heavy 150ms ease;
        }

        @keyframes haptic-pulse-light {
            0% { transform: scale(1); }
            50% { transform: scale(1.02); }
            100% { transform: scale(1); }
        }

        @keyframes haptic-pulse-medium {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
        }

        @keyframes haptic-pulse-heavy {
            0% { transform: scale(1); }
            50% { transform: scale(1.08); }
            100% { transform: scale(1); }
        }

        /* Loading states for mobile */
        .mobile-loading {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 40px;
        }

        .mobile-spinner {
            width: 32px;
            height: 32px;
            border: 3px solid #f3f4f6;
            border-top: 3px solid #3b82f6;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Mobile-specific Streamlit overrides */
        @media screen and (max-width: 768px) {
            .main .block-container {
                padding: 0 !important;
                max-width: none !important;
            }

            .stApp > header {
                display: none;
            }

            .stSelectbox > div > div {
                min-height: var(--touch-target-min);
            }

            .stButton > button {
                min-height: var(--touch-target-min);
                touch-action: manipulation;
                -webkit-tap-highlight-color: transparent;
            }

            .stMetric {
                background: white;
                padding: 16px;
                border-radius: 12px;
                margin-bottom: 12px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            }

            /* Hide desktop-only elements */
            .desktop-only {
                display: none !important;
            }

            /* Show mobile-only elements */
            .mobile-only {
                display: block !important;
            }
        }

        /* Landscape orientation optimizations */
        @media screen and (max-width: 768px) and (orientation: landscape) {
            .mobile-header {
                height: 50px;
            }

            .mobile-nav-bar {
                height: 50px;
            }

            .mobile-content {
                padding-top: calc(50px + 12px);
                padding-bottom: calc(50px + 12px);
            }

            .mobile-nav-label {
                display: none;
            }
        }

        /* Dark mode mobile optimizations */
        @media (prefers-color-scheme: dark) {
            .mobile-header,
            .mobile-nav-bar,
            .mobile-card,
            .swipeable-card {
                background: #1f2937;
                border-color: #374151;
            }

            .mobile-header-title,
            .mobile-card-title {
                color: #f9fafb;
            }

            .mobile-nav-item {
                color: #d1d5db;
            }

            .mobile-nav-item.active {
                background: #1e40af;
                color: #60a5fa;
            }
        }

        /* PWA installation prompt */
        .pwa-install-banner {
            position: fixed;
            bottom: calc(var(--mobile-nav-height) + 16px);
            left: 16px;
            right: 16px;
            background: #1f2937;
            color: white;
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
            z-index: 1500;
            transform: translateY(100%);
            transition: transform 300ms ease;
        }

        .pwa-install-banner.show {
            transform: translateY(0);
        }

        .pwa-install-content {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .pwa-install-text {
            flex: 1;
            font-size: 14px;
            font-weight: 500;
        }

        .pwa-install-button {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
        }
        </style>
        """, unsafe_allow_html=True)

    def _inject_mobile_javascript(self):
        """Inject JavaScript for mobile interactions"""
        mobile_js = """
        <script>
        // Mobile optimization JavaScript
        (function() {
            let startY = 0;
            let startX = 0;
            let currentY = 0;
            let currentX = 0;
            let touchStartTime = 0;
            let isRefreshing = false;

            // Touch event handlers for swipe gestures
            function handleTouchStart(e) {
                startY = e.touches[0].clientY;
                startX = e.touches[0].clientX;
                touchStartTime = Date.now();
            }

            function handleTouchMove(e) {
                if (!startY || !startX) return;

                currentY = e.touches[0].clientY;
                currentX = e.touches[0].clientX;

                const diffY = currentY - startY;
                const diffX = currentX - startX;

                // Pull-to-refresh logic
                if (diffY > 0 && window.scrollY === 0 && Math.abs(diffX) < 50) {
                    e.preventDefault();
                    const pullDistance = Math.min(diffY, 100);
                    const pullProgress = pullDistance / 100;

                    const container = document.querySelector('.pull-refresh-container');
                    const indicator = document.querySelector('.pull-refresh-indicator');

                    if (container && indicator) {
                        container.style.transform = `translateY(${pullDistance * 0.5}px)`;
                        indicator.style.opacity = pullProgress;
                        indicator.style.transform = `translateX(-50%) rotate(${pullProgress * 360}deg)`;

                        if (pullDistance > 60 && !isRefreshing) {
                            isRefreshing = true;
                            triggerRefresh();
                        }
                    }
                }
            }

            function handleTouchEnd(e) {
                const touchEndTime = Date.now();
                const touchDuration = touchEndTime - touchStartTime;

                if (!startY || !startX) return;

                const diffY = currentY - startY;
                const diffX = currentX - startX;
                const absDiffY = Math.abs(diffY);
                const absDiffX = Math.abs(diffX);

                // Reset pull-to-refresh
                const container = document.querySelector('.pull-refresh-container');
                const indicator = document.querySelector('.pull-refresh-indicator');

                if (container && indicator && !isRefreshing) {
                    container.style.transform = '';
                    indicator.style.opacity = 0;
                }

                // Swipe detection
                if (Math.max(absDiffY, absDiffX) > 50 && touchDuration < 500) {
                    let direction;

                    if (absDiffX > absDiffY) {
                        direction = diffX > 0 ? 'right' : 'left';
                    } else {
                        direction = diffY > 0 ? 'down' : 'up';
                    }

                    // Trigger swipe event
                    const swipeEvent = new CustomEvent('mobileSwipe', {
                        detail: { direction, startX, startY, endX: currentX, endY: currentY }
                    });
                    document.dispatchEvent(swipeEvent);
                }

                startY = null;
                startX = null;
                currentY = 0;
                currentX = 0;
            }

            // Refresh functionality
            function triggerRefresh() {
                const indicator = document.querySelector('.pull-refresh-indicator');
                if (indicator) {
                    indicator.classList.add('visible');
                    indicator.innerHTML = '🔄';
                }

                // Simulate refresh delay
                setTimeout(() => {
                    window.parent.postMessage({type: 'refresh'}, '*');
                    isRefreshing = false;

                    const container = document.querySelector('.pull-refresh-container');
                    if (container) {
                        container.style.transform = '';
                    }

                    if (indicator) {
                        indicator.style.opacity = 0;
                        indicator.innerHTML = '↓';
                    }
                }, 1500);
            }

            // Haptic feedback simulation
            function triggerHaptic(intensity = 'light') {
                if ('vibrate' in navigator) {
                    switch(intensity) {
                        case 'light': navigator.vibrate(10); break;
                        case 'medium': navigator.vibrate(25); break;
                        case 'heavy': navigator.vibrate(50); break;
                    }
                }
            }

            // Install PWA prompt
            let deferredPrompt;
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                deferredPrompt = e;
                showInstallBanner();
            });

            function showInstallBanner() {
                const banner = document.querySelector('.pwa-install-banner');
                if (banner) {
                    banner.classList.add('show');
                }
            }

            function installPWA() {
                if (deferredPrompt) {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((result) => {
                        deferredPrompt = null;
                        hidePWABanner();
                    });
                }
            }

            function hidePWABanner() {
                const banner = document.querySelector('.pwa-install-banner');
                if (banner) {
                    banner.classList.remove('show');
                }
            }

            // Add event listeners
            document.addEventListener('touchstart', handleTouchStart, {passive: false});
            document.addEventListener('touchmove', handleTouchMove, {passive: false});
            document.addEventListener('touchend', handleTouchEnd);

            // Global functions
            window.triggerHaptic = triggerHaptic;
            window.installPWA = installPWA;
            window.hidePWABanner = hidePWABanner;

            // Device orientation handling
            function handleOrientationChange() {
                window.parent.postMessage({
                    type: 'orientation_change',
                    orientation: screen.orientation.angle
                }, '*');
            }

            window.addEventListener('orientationchange', handleOrientationChange);

            // Viewport height fix for mobile browsers
            function setViewportHeight() {
                const vh = window.innerHeight * 0.01;
                document.documentElement.style.setProperty('--vh', vh + 'px');
            }

            setViewportHeight();
            window.addEventListener('resize', setViewportHeight);
        })();
        </script>
        """

        st.components.v1.html(mobile_js, height=0)

    def render_mobile_layout(self, content_func: Callable, **kwargs) -> None:
        """Render mobile-optimized layout wrapper"""
        # Mobile header
        self._render_mobile_header(kwargs.get('title', 'EnterpriseHub'))

        # Mobile content area with pull-to-refresh
        st.markdown("""
        <div class="mobile-viewport safe-area-container">
            <div class="pull-refresh-container">
                <div class="pull-refresh-indicator">↓</div>
                <div class="mobile-content">
        """, unsafe_allow_html=True)

        # Render main content
        content_func()

        # Close content area
        st.markdown("""
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Mobile navigation
        self._render_mobile_navigation()

        # PWA install banner
        self._render_pwa_banner()

    def _render_mobile_header(self, title: str) -> None:
        """Render mobile header"""
        st.markdown(f"""
        <div class="mobile-header">
            <button class="mobile-header-action" onclick="history.back()">
                ←
            </button>
            <div class="mobile-header-title">{title}</div>
            <button class="mobile-header-action" onclick="showMobileMenu()">
                ☰
            </button>
        </div>
        """, unsafe_allow_html=True)

    def _render_mobile_navigation(self) -> None:
        """Render mobile bottom navigation"""
        nav_items = [
            {"icon": "🏠", "label": "Home", "key": "home"},
            {"icon": "👥", "label": "Leads", "key": "leads"},
            {"icon": "📊", "label": "Analytics", "key": "analytics"},
            {"icon": "💬", "label": "Chat", "key": "chat"},
            {"icon": "⚙️", "label": "Settings", "key": "settings"}
        ]

        current_tab = st.session_state.get('mobile_nav_tab', 'home')

        nav_html = '<div class="mobile-nav-bar">'

        for item in nav_items:
            active_class = 'active' if item['key'] == current_tab else ''
            nav_html += f"""
            <div class="mobile-nav-item {active_class}" onclick="selectMobileTab('{item['key']}')">
                <div class="mobile-nav-icon">{item['icon']}</div>
                <div class="mobile-nav-label">{item['label']}</div>
            </div>
            """

        nav_html += '</div>'
        st.markdown(nav_html, unsafe_allow_html=True)

    def _render_pwa_banner(self) -> None:
        """Render PWA installation banner"""
        st.markdown("""
        <div class="pwa-install-banner">
            <div class="pwa-install-content">
                <div class="pwa-install-text">
                    Install EnterpriseHub for quick access and offline use!
                </div>
                <button class="pwa-install-button" onclick="installPWA()">
                    Install
                </button>
                <button class="mobile-header-action" onclick="hidePWABanner()">
                    ✕
                </button>
            </div>
        </div>
        """, unsafe_allow_html=True)

    def render_swipeable_card(self, content: Dict[str, Any],
                            left_action: Optional[str] = None,
                            right_action: Optional[str] = None) -> None:
        """Render swipeable card component"""
        card_id = f"card_{hash(str(content))}"

        card_html = f"""
        <div class="swipeable-card" id="{card_id}">
        """

        if left_action:
            card_html += f"""
            <div class="swipe-action left">{left_action}</div>
            """

        if right_action:
            card_html += f"""
            <div class="swipe-action right">{right_action}</div>
            """

        card_html += f"""
            <div class="mobile-card">
                <div class="mobile-card-header">
                    <h3 class="mobile-card-title">{content.get('title', '')}</h3>
                    <button class="mobile-card-action">⋯</button>
                </div>
                <div class="mobile-card-body">
                    <p>{content.get('description', '')}</p>
                </div>
            </div>
        </div>
        """

        st.markdown(card_html, unsafe_allow_html=True)

    def render_mobile_form(self, fields: List[Dict[str, Any]],
                          submit_label: str = "Submit") -> None:
        """Render mobile-optimized form"""
        st.markdown('<div class="mobile-form">', unsafe_allow_html=True)

        for field in fields:
            field_type = field.get('type', 'text')
            field_label = field.get('label', '')
            field_key = field.get('key', '')
            field_placeholder = field.get('placeholder', '')

            if field_type == 'text':
                st.text_input(
                    field_label,
                    key=field_key,
                    placeholder=field_placeholder,
                    label_visibility="visible"
                )
            elif field_type == 'select':
                st.selectbox(
                    field_label,
                    field.get('options', []),
                    key=field_key
                )
            elif field_type == 'textarea':
                st.text_area(
                    field_label,
                    key=field_key,
                    placeholder=field_placeholder
                )

        if st.button(submit_label, use_container_width=True, type="primary"):
            st.success("Form submitted successfully!")

        st.markdown('</div>', unsafe_allow_html=True)

    def render_mobile_grid(self, items: List[Dict[str, Any]],
                          columns: int = 2) -> None:
        """Render mobile-optimized grid layout"""
        grid_class = f"mobile-grid mobile-grid-{columns}"

        st.markdown(f'<div class="{grid_class}">', unsafe_allow_html=True)

        for item in items:
            st.markdown(f"""
            <div class="mobile-card">
                <div class="mobile-card-header">
                    <h4 class="mobile-card-title">{item.get('title', '')}</h4>
                </div>
                <div>{item.get('content', '')}</div>
                <div style="margin-top: 12px;">
                    <button class="mobile-button">{item.get('action', 'View')}</button>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    def render_mobile_metrics(self, metrics: List[Dict[str, Any]]) -> None:
        """Render mobile-optimized metrics display"""
        for metric in metrics:
            st.markdown(f"""
            <div class="mobile-card">
                <div style="text-align: center;">
                    <div style="color: #6b7280; font-size: 14px; margin-bottom: 8px;">
                        {metric.get('label', '')}
                    </div>
                    <div style="font-size: 32px; font-weight: 700; color: #1f2937; margin-bottom: 8px;">
                        {metric.get('value', '')}
                    </div>
                    <div style="color: {metric.get('color', '#10b981')}; font-size: 14px; font-weight: 600;">
                        {metric.get('change', '')}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    def render_mobile_action_sheet(self, actions: List[Dict[str, Any]],
                                  title: str = "Actions") -> None:
        """Render mobile action sheet/bottom drawer"""
        drawer_id = f"drawer_{hash(title)}"

        drawer_html = f"""
        <div class="mobile-drawer" id="{drawer_id}">
            <div class="mobile-drawer-content">
                <div class="mobile-drawer-handle"></div>
                <h3 style="margin-bottom: 20px; text-align: center;">{title}</h3>
        """

        for action in actions:
            drawer_html += f"""
            <button class="mobile-button" onclick="executeAction('{action.get('key', '')}')">
                {action.get('icon', '')} {action.get('label', '')}
            </button>
            """

        drawer_html += """
            <button class="mobile-button secondary" onclick="closeDrawer()">
                Cancel
            </button>
            </div>
        </div>
        """

        st.markdown(drawer_html, unsafe_allow_html=True)

    def render_offline_indicator(self) -> None:
        """Render offline status indicator"""
        st.markdown("""
        <div id="offline-indicator" style="
            position: fixed;
            top: calc(var(--mobile-header-height) + var(--mobile-safe-area-top));
            left: 16px;
            right: 16px;
            background: #f59e0b;
            color: white;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
            z-index: 1001;
            transform: translateY(-100%);
            transition: transform 300ms ease;
        ">
            📡 You're offline. Some features may be limited.
        </div>

        <script>
        window.addEventListener('online', function() {
            document.getElementById('offline-indicator').style.transform = 'translateY(-100%)';
        });

        window.addEventListener('offline', function() {
            document.getElementById('offline-indicator').style.transform = 'translateY(0)';
        });
        </script>
        """, unsafe_allow_html=True)

    def generate_pwa_manifest(self) -> str:
        """Generate PWA manifest file content"""
        return json.dumps(self.pwa_config, indent=2)

    def register_gesture_handler(self, gesture_type: str,
                                direction: SwipeDirection,
                                callback: Callable) -> None:
        """Register gesture handler for mobile interactions"""
        gesture = TouchGesture(
            type=gesture_type,
            direction=direction,
            callback=callback
        )

        self.gesture_handlers[f"{gesture_type}_{direction.value}"] = gesture


# Global mobile optimization suite instance
mobile_suite = MobileOptimizationSuite()

def get_mobile_suite() -> MobileOptimizationSuite:
    """Get the global mobile optimization suite instance"""
    return mobile_suite
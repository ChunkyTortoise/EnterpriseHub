/**
 * Theme Configuration
 * Comprehensive design system for the mobile app
 */

import {DefaultTheme} from '@react-navigation/native';

export const theme = {
  // Color Palette
  colors: {
    // Primary Brand Colors
    primary: '#6D28D9',      // Purple - main brand color
    primaryLight: '#8B5CF6',  // Light purple
    primaryDark: '#4C1D95',   // Dark purple

    // Secondary Colors
    secondary: '#10B981',     // Green - success/growth
    secondaryLight: '#34D399',
    secondaryDark: '#059669',

    // Accent Colors
    accent: '#F59E0B',        // Amber - attention/warnings
    accentLight: '#FCD34D',
    accentDark: '#D97706',

    // Status Colors
    success: '#10B981',       // Green
    warning: '#F59E0B',       // Amber
    error: '#EF4444',         // Red
    info: '#3B82F6',          // Blue

    // Neutral Colors
    background: '#FFFFFF',     // Main background
    surface: '#F8FAFC',        // Card/surface background
    surfaceLight: '#FFFFFF',   // Light surface
    surfaceDark: '#F1F5F9',    // Darker surface

    // Text Colors
    text: '#1F2937',          // Primary text
    textSecondary: '#6B7280',  // Secondary text
    textLight: '#9CA3AF',      // Light/placeholder text
    textInverse: '#FFFFFF',    // White text

    // Border Colors
    border: '#E5E7EB',        // Light border
    borderDark: '#D1D5DB',    // Darker border
    borderLight: '#F3F4F6',   // Very light border

    // Utility Colors
    white: '#FFFFFF',
    black: '#000000',
    transparent: 'transparent',

    // Gradient Colors (for special elements)
    gradient: {
      primary: ['#6D28D9', '#8B5CF6'],
      secondary: ['#10B981', '#34D399'],
      sunset: ['#F59E0B', '#EF4444'],
    },

    // Real Estate Specific Colors
    realEstate: {
      luxury: '#8B5CF6',       // Purple for luxury properties
      commercial: '#3B82F6',    // Blue for commercial
      residential: '#10B981',   // Green for residential
      investment: '#F59E0B',    // Amber for investment opportunities
    },
  },

  // Typography
  fonts: {
    // Font Families
    light: 'System', // iOS: San Francisco, Android: Roboto
    regular: 'System',
    medium: 'SystemMedium',
    semiBold: 'SystemSemiBold',
    bold: 'SystemBold',

    // Font Sizes
    sizes: {
      xs: 10,
      sm: 12,
      md: 14,
      lg: 16,
      xl: 18,
      xxl: 20,
      xxxl: 24,
      heading: 28,
      title: 32,
      display: 40,
    },

    // Line Heights
    lineHeights: {
      xs: 14,
      sm: 16,
      md: 20,
      lg: 24,
      xl: 28,
      xxl: 32,
      xxxl: 36,
      heading: 40,
      title: 44,
      display: 52,
    },
  },

  // Spacing Scale
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 40,
    xxxl: 48,
  },

  // Border Radius
  borderRadius: {
    none: 0,
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    xxl: 20,
    round: 9999,
  },

  // Shadows
  shadows: {
    sm: {
      shadowColor: '#000000',
      shadowOffset: {width: 0, height: 1},
      shadowOpacity: 0.05,
      shadowRadius: 2,
      elevation: 1,
    },
    md: {
      shadowColor: '#000000',
      shadowOffset: {width: 0, height: 2},
      shadowOpacity: 0.1,
      shadowRadius: 4,
      elevation: 3,
    },
    lg: {
      shadowColor: '#000000',
      shadowOffset: {width: 0, height: 4},
      shadowOpacity: 0.15,
      shadowRadius: 8,
      elevation: 6,
    },
    xl: {
      shadowColor: '#000000',
      shadowOffset: {width: 0, height: 8},
      shadowOpacity: 0.2,
      shadowRadius: 16,
      elevation: 10,
    },
  },

  // Animation Durations
  animations: {
    fast: 150,
    normal: 250,
    slow: 400,
  },

  // Component Specific Styles
  components: {
    // Button variants
    button: {
      height: {
        sm: 32,
        md: 40,
        lg: 48,
        xl: 56,
      },
      padding: {
        sm: 8,
        md: 12,
        lg: 16,
        xl: 20,
      },
    },

    // Input variants
    input: {
      height: {
        sm: 36,
        md: 44,
        lg: 52,
      },
      padding: {
        horizontal: 12,
        vertical: 8,
      },
    },

    // Card variants
    card: {
      padding: 16,
      borderRadius: 12,
    },
  },

  // Navigation Theme (React Navigation)
  navigation: {
    ...DefaultTheme,
    colors: {
      ...DefaultTheme.colors,
      primary: '#6D28D9',
      background: '#FFFFFF',
      card: '#FFFFFF',
      text: '#1F2937',
      border: '#E5E7EB',
      notification: '#EF4444',
    },
  },

  // Screen Dimensions Helpers
  layout: {
    isSmallDevice: false, // Will be set dynamically
    isTablet: false,      // Will be set dynamically
    headerHeight: 64,
    tabBarHeight: 60,
    statusBarHeight: 44,  // iOS default, Android varies
  },

  // Accessibility
  accessibility: {
    minTouchSize: 44,     // Minimum touch target size
  },

  // Real Estate App Specific
  realEstate: {
    propertyCard: {
      imageHeight: 200,
      borderRadius: 12,
      padding: 16,
    },
    leadCard: {
      height: 120,
      borderRadius: 8,
      padding: 12,
    },
    dashboard: {
      metricCardHeight: 100,
      quickActionSize: 80,
    },
  },
};

// Theme helper functions
export const getColor = (colorPath: string) => {
  const keys = colorPath.split('.');
  let value: any = theme.colors;

  for (const key of keys) {
    value = value[key];
    if (value === undefined) return theme.colors.primary;
  }

  return value;
};

export const getShadow = (level: 'sm' | 'md' | 'lg' | 'xl') => {
  return theme.shadows[level];
};

export const getSpacing = (size: keyof typeof theme.spacing) => {
  return theme.spacing[size];
};

// Type definitions for TypeScript
export type ThemeColors = typeof theme.colors;
export type ThemeFonts = typeof theme.fonts;
export type ThemeSpacing = typeof theme.spacing;
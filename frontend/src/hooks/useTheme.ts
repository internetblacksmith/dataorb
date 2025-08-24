import { useCallback, useEffect } from 'react';
import { Theme } from '../types';
import { CSS_VARIABLES, API_ENDPOINTS, THEME_DEFAULTS } from '../constants';

/**
 * Custom hook for theme management
 */
export const useTheme = (themeId?: string) => {
  const applyTheme = useCallback(async (id: string) => {
    // Skip for default themes
    if (!id || Object.values(THEME_DEFAULTS).includes(id as any)) {
      document.documentElement.setAttribute('data-theme', id || THEME_DEFAULTS.DARK);
      return;
    }

    try {
      let themeData: Theme;
      
      // Check for embedded theme data first
      if ((window as any).__INITIAL_DATA__?.theme) {
        themeData = (window as any).__INITIAL_DATA__.theme;
        // Clear the initial theme data after using it
        delete (window as any).__INITIAL_DATA__.theme;
      } else {
        // Fetch custom theme if not embedded
        const response = await fetch(API_ENDPOINTS.THEME_BY_ID(id));
        if (!response.ok) return;
        themeData = await response.json();
      }
      const root = document.documentElement;

      // Map theme colors to CSS variables if colors exist
      if (themeData.colors) {
        const cssVarMap: Record<string, string> = {
          BG_GRADIENT: 'background',
          CONTAINER_BG: 'containerBg',
          TEXT_COLOR: 'text',
          TEXT_SECONDARY: 'textSecondary',
          ACCENT: 'accent',
          ACCENT_SECONDARY: 'accentSecondary',
          BORDER: 'border',
          SHADOW: 'shadow',
          STAT_BG: 'statBg',
          STAT_BORDER: 'statBorder',
          STAT_VALUE: 'statValue',
          STAT_LABEL: 'statLabel',
          GLOW_PRIMARY: 'glowPrimary',
          GLOW_SECONDARY: 'glowSecondary',
          STATUS_DOT: 'statusDot',
          TREND_UP: 'trendUp',
          TREND_DOWN: 'trendDown',
        };

        // Apply CSS variables
        Object.entries(cssVarMap).forEach(([cssVar, themeKey]) => {
          const value = (themeData.colors as any)[themeKey];
          if (value) {
            root.style.setProperty(CSS_VARIABLES[cssVar as keyof typeof CSS_VARIABLES], value);
          }
        });
      }

      // Remove data-theme attribute for custom themes
      root.removeAttribute('data-theme');
    } catch (err) {
      // Silently fall back to default theme
      document.documentElement.setAttribute('data-theme', THEME_DEFAULTS.DARK);
    }
  }, []);

  // Apply theme on mount and when it changes
  useEffect(() => {
    if (themeId) {
      applyTheme(themeId);
    }
    // Ensure theme loaded attribute is set
    document.body.setAttribute('data-theme-loaded', 'true');
  }, [themeId, applyTheme]);

  return { applyTheme };
};
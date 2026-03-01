import { useState, useEffect } from 'react';
import { Theme } from '../types';
import { API_ENDPOINTS } from '../constants';

export const useThemeData = (theme: string | undefined): Theme | null => {
  const [themeData, setThemeData] = useState<Theme | null>(null);

  useEffect(() => {
    if ((window as any).__INITIAL_DATA__?.theme) {
      setThemeData((window as any).__INITIAL_DATA__.theme);
      delete (window as any).__INITIAL_DATA__.theme;
      return;
    }

    if (!theme || ['dark', 'light'].includes(theme)) {
      setThemeData(null);
      return;
    }

    const loadThemeData = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.THEME_BY_ID(theme));
        if (response.ok) {
          setThemeData(await response.json());
        }
      } catch {
        // Theme loading is non-critical
      }
    };

    loadThemeData();
  }, [theme]);

  return themeData;
};

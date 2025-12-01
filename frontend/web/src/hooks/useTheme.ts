import { useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

const THEME_KEY = 'train-control-theme';

/**
 * Custom hook for managing theme state
 * Persists to localStorage and applies to document root
 */
export const useTheme = () => {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem(THEME_KEY);
    return (stored as Theme) || 'system';
  });

  useEffect(() => {
    const root = window.document.documentElement;

    // Remove existing theme classes
    root.classList.remove('light', 'dark');

    if (theme === 'system') {
      const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
      root.classList.add(systemTheme);
    } else {
      root.classList.add(theme);
    }

    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  return { theme, setTheme };
};

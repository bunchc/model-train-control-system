import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTheme } from '@/hooks/useTheme';
import { APP_NAME } from '@/utils/constants';
import {
  HomeIcon,
  Cog6ToothIcon,
  ServerIcon,
  SunIcon,
  MoonIcon,
  ComputerDesktopIcon,
} from '@heroicons/react/24/outline';

/**
 * Application header with navigation and theme toggle
 */
export const Header: React.FC = () => {
  const { theme, setTheme } = useTheme();
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: HomeIcon },
    { name: 'Configuration', href: '/config', icon: Cog6ToothIcon },
    { name: 'Controllers', href: '/controllers', icon: ServerIcon },
  ];

  const cycleTheme = () => {
    const themes: Array<'light' | 'dark' | 'system'> = ['light', 'dark', 'system'];
    const currentIndex = themes.indexOf(theme);
    const nextIndex = (currentIndex + 1) % themes.length;
    setTheme(themes[nextIndex]);
  };

  const ThemeIcon = theme === 'light' ? SunIcon : theme === 'dark' ? MoonIcon : ComputerDesktopIcon;

  return (
    <header className="sticky top-0 z-40 border-b border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <nav className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2">
              <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center">
                <span className="text-white font-bold text-lg">T</span>
              </div>
              <span className="hidden text-lg font-semibold text-gray-900 dark:text-gray-100 sm:block">
                {APP_NAME}
              </span>
            </Link>
          </div>

          {/* Navigation */}
          <div className="flex items-center gap-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-50 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300'
                      : 'text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <item.icon className="h-5 w-5" aria-hidden="true" />
                  <span className="hidden sm:inline">{item.name}</span>
                </Link>
              );
            })}

            {/* Theme Toggle */}
            <button
              onClick={cycleTheme}
              className="ml-4 rounded-md p-2 text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
              aria-label={`Current theme: ${theme}. Click to change theme.`}
            >
              <ThemeIcon className="h-5 w-5" aria-hidden="true" />
            </button>
          </div>
        </div>
      </nav>
    </header>
  );
};

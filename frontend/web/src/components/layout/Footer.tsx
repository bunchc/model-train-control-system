import React from 'react';
import { APP_VERSION } from '@/utils/constants';

/**
 * Application footer
 */
export const Footer: React.FC = () => {
  return (
    <footer className="border-t border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Model Train Control System v{APP_VERSION}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            © {new Date().getFullYear()} All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
};

import React from 'react';
import { Link } from 'react-router-dom';
import { PageLayout } from '@/components/layout/PageLayout';
import { HomeIcon } from '@heroicons/react/24/outline';

/**
 * 404 Not Found page
 */
export const NotFound: React.FC = () => {
  return (
    <PageLayout>
      <div className="flex min-h-[60vh] flex-col items-center justify-center text-center">
        <h1 className="text-9xl font-bold text-gray-200 dark:text-gray-700">404</h1>
        <h2 className="mt-4 text-2xl font-semibold text-gray-900 dark:text-gray-100">Page Not Found</h2>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex items-center gap-2 rounded-md bg-blue-600 px-4 py-2 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          <HomeIcon className="h-5 w-5" aria-hidden="true" />
          Go to Dashboard
        </Link>
      </div>
    </PageLayout>
  );
};

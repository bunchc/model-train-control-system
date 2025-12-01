import React from 'react';
import { PageLayout } from '@/components/layout/PageLayout';

/**
 * Configuration page (placeholder for future implementation)
 */
export const Configuration: React.FC = () => {
  return (
    <PageLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Configuration</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Manage edge controllers, plugins, and system settings.
          </p>
        </div>

        <div className="rounded-lg border-2 border-dashed border-gray-300 bg-gray-50 p-12 text-center dark:border-gray-700 dark:bg-gray-800">
          <p className="text-gray-600 dark:text-gray-400">Configuration UI coming soon...</p>
        </div>
      </div>
    </PageLayout>
  );
};

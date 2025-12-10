import React from 'react';
import { PageLayout } from '@/components/layout/PageLayout';
import { useControllers } from '@/api/queries';
import { ControllerGrid } from '@/components/controllers/ControllerGrid';
import { LoadingState } from '@/components/common/LoadingState';

/**
 * Controllers page - displays edge controller status and telemetry
 */
export const Controllers: React.FC = () => {
  const { data: controllers, isLoading, error } = useControllers();

  return (
    <PageLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Edge Controllers</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            View and manage edge controllers.
          </p>
        </div>

        {error ? (
          <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/20">
            <p className="text-sm text-red-800 dark:text-red-400">
              Failed to load controllers: {error instanceof Error ? error.message : 'Unknown error'}
            </p>
          </div>
        ) : isLoading ? (
          <LoadingState />
        ) : (
          <ControllerGrid controllers={controllers || []} />
        )}
      </div>
    </PageLayout>
  );
};

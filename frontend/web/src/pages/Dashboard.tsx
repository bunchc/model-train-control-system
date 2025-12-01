import React from 'react';
import { PageLayout } from '@/components/layout/PageLayout';
import { TrainGrid } from '@/components/trains/TrainGrid';
import { LoadingState } from '@/components/common/LoadingState';
import { useTrains } from '@/api/queries';
import { ExclamationCircleIcon } from '@heroicons/react/24/outline';

/**
 * Dashboard page - Main landing page with all trains
 */
export const Dashboard: React.FC = () => {
  const { data: trains, isLoading, error } = useTrains();

  return (
    <PageLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Dashboard</h1>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Monitor and control your model trains in real-time.
          </p>
        </div>

        {/* Stats */}
        {trains && (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <StatCard label="Total Trains" value={trains.length} />
            <StatCard label="Active Trains" value={trains.filter((t) => t.plugin).length} />
            <StatCard label="Configured Plugins" value={new Set(trains.map((t) => t.plugin.name)).size} />
          </div>
        )}

        {/* Trains Grid */}
        {isLoading && <LoadingState message="Loading trains..." />}

        {error && (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-900/20">
            <div className="flex items-center gap-3">
              <ExclamationCircleIcon className="h-6 w-6 text-red-600 dark:text-red-400" aria-hidden="true" />
              <div>
                <h3 className="font-semibold text-red-900 dark:text-red-200">Failed to load trains</h3>
                <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error.message}</p>
              </div>
            </div>
          </div>
        )}

        {trains && <TrainGrid trains={trains} />}
      </div>
    </PageLayout>
  );
};

interface StatCardProps {
  label: string;
  value: number;
}

const StatCard: React.FC<StatCardProps> = ({ label, value }) => {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm dark:border-gray-700 dark:bg-gray-800">
      <div className="text-sm font-medium text-gray-600 dark:text-gray-400">{label}</div>
      <div className="mt-2 text-3xl font-bold text-gray-900 dark:text-gray-100">{value}</div>
    </div>
  );
};

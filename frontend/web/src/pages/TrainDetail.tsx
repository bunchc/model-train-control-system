import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { PageLayout } from '@/components/layout/PageLayout';
import { LoadingState } from '@/components/common/LoadingState';
import { TelemetryDisplay } from '@/components/trains/TelemetryDisplay';
import { ControlPanel } from '@/components/trains/ControlPanel';
import { useTrains, useTrainStatus } from '@/api/queries';
import { ArrowLeftIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

/**
 * Train detail page with telemetry and controls
 */
export const TrainDetail: React.FC = () => {
  const { trainId } = useParams<{ trainId: string }>();
  const { data: trains, isLoading: trainsLoading } = useTrains();
  const { data: status, isLoading: statusLoading, error } = useTrainStatus(trainId!);

  const train = trains?.find((t) => t.id === trainId);

  if (trainsLoading || statusLoading) {
    return (
      <PageLayout>
        <LoadingState message="Loading train details..." />
      </PageLayout>
    );
  }

  if (!train) {
    return (
      <PageLayout>
        <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-900/20">
          <div className="flex items-center gap-3">
            <ExclamationCircleIcon className="h-6 w-6 text-red-600 dark:text-red-400" aria-hidden="true" />
            <div>
              <h3 className="font-semibold text-red-900 dark:text-red-200">Train not found</h3>
              <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                The train with ID "{trainId}" does not exist.
              </p>
            </div>
          </div>
          <Link
            to="/"
            className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-red-700 hover:text-red-900 dark:text-red-300 dark:hover:text-red-100"
          >
            <ArrowLeftIcon className="h-4 w-4" aria-hidden="true" />
            Back to Dashboard
          </Link>
        </div>
      </PageLayout>
    );
  }

  const isOnline = !!status && !error;

  return (
    <PageLayout>
      <div className="space-y-6">
        {/* Breadcrumb */}
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm font-medium text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
        >
          <ArrowLeftIcon className="h-4 w-4" aria-hidden="true" />
          Back to Dashboard
        </Link>

        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{train.name}</h1>
          {train.description && (
            <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{train.description}</p>
          )}
          <div className="mt-2 flex flex-wrap gap-2 text-sm text-gray-500 dark:text-gray-400">
            <span>ID: {train.id}</span>
            <span>•</span>
            <span>Plugin: {train.plugin.name}</span>
            {train.model && (
              <>
                <span>•</span>
                <span>Model: {train.model}</span>
              </>
            )}
          </div>
        </div>

        {/* Error State */}
        {error && (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-800 dark:bg-yellow-900/20">
            <p className="text-sm text-yellow-800 dark:text-yellow-300">
              Unable to fetch train status. The train may be offline or experiencing connectivity issues.
            </p>
          </div>
        )}

        {/* Main Content: Telemetry + Controls */}
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          {/* Telemetry */}
          <div>
            {status ? (
              <TelemetryDisplay status={status} />
            ) : (
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-12 text-center dark:border-gray-700 dark:bg-gray-800">
                <p className="text-gray-600 dark:text-gray-400">No telemetry data available</p>
              </div>
            )}
          </div>

          {/* Controls */}
          <div>
            <ControlPanel trainId={train.id} currentSpeed={status?.speed ?? 0} isOnline={isOnline} />
          </div>
        </div>
      </div>
    </PageLayout>
  );
};

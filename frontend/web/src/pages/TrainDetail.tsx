import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { PageLayout } from '@/components/layout/PageLayout';
import { LoadingState } from '@/components/common/LoadingState';
import { TelemetryDisplay } from '@/components/trains/TelemetryDisplay';
import { ControlPanel } from '@/components/trains/ControlPanel';
import { TrainConfigModal } from '@/components/trains/TrainConfigModal';
import { useTrains, useTrainStatus } from '@/api/queries';
import { ArrowLeftIcon, ExclamationCircleIcon, CogIcon } from '@heroicons/react/24/outline';

/**
 * Train detail page with telemetry and controls
 */
export const TrainDetail: React.FC = () => {
  const { trainId } = useParams<{ trainId: string }>();
  const { data: trains, isLoading: trainsLoading } = useTrains();
  const { data: status, isLoading: statusLoading, error } = useTrainStatus(trainId!);
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);

  const train = trains?.find((t) => t.id === trainId);

  if (trainsLoading) {
    return <LoadingState />;
  }

  if (!train) {
    return (
      <PageLayout>
        <div className="p-6">
          <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/20">
            <div className="flex">
              <ExclamationCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Train not found
                </h3>
                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                  <p>No train found with ID: {trainId}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </PageLayout>
    );
  }

  // Handle status loading states and errors separately
  const isStatusNotFound = (error: any) => {
    return error?.response?.status === 404 || error?.message?.includes('404');
  };

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
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{train.name}</h1>
              <button
                onClick={() => setIsConfigModalOpen(true)}
                className="rounded-md p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-800 dark:hover:text-gray-300"
                aria-label="Configure train"
                title="Configure train"
              >
                <CogIcon className="h-6 w-6" />
              </button>
            </div>
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
        </div>

        {/* Error State */}
        {error && (
          <div className="rounded-lg border border-yellow-200 bg-yellow-50 p-4 dark:border-yellow-800 dark:bg-yellow-900/20">
            <p className="text-sm text-yellow-800 dark:text-yellow-300">
              {isStatusNotFound(error)
                ? 'No telemetry available yet. Send a command to initialize the train status.'
                : 'Unable to fetch train status. The train may be offline or experiencing connectivity issues.'}
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
            <ControlPanel
              trainId={train.id}
              currentSpeed={status?.speed ?? 0}
              isOnline={isOnline}
              invertDirections={train.invert_directions}
            />
          </div>
        </div>
      </div>

      {/* Config Modal */}
      <TrainConfigModal isOpen={isConfigModalOpen} onClose={() => setIsConfigModalOpen(false)} train={train} />
    </PageLayout>
  );
};

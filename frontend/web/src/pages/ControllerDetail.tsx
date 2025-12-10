import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { PageLayout } from '@/components/layout/PageLayout';
import { LoadingState } from '@/components/common/LoadingState';
import { InfoCard } from '@/components/common/InfoCard';
import { StatusBadge } from '@/components/common/StatusBadge';
import { AssignedTrainsTable } from '@/components/controllers/AssignedTrainsTable';
import { useController } from '@/api/queries';
import { formatRelativeTime } from '@/utils/formatting';
import { calculateControllerStatus } from '@/utils/controllerStatus';
import { ArrowLeftIcon, ExclamationCircleIcon } from '@heroicons/react/24/outline';

/**
 * Controller detail page with comprehensive controller information,
 * system metrics, and assigned trains table.
 */
export const ControllerDetail: React.FC = () => {
  const { controllerId } = useParams<{ controllerId: string }>();
  const { data: controller, isLoading, error } = useController(controllerId!);

  // Calculate display status based on last_seen timestamp
  const displayStatus = controller ? calculateControllerStatus(controller.last_seen) : 'unknown';

  if (isLoading) {
    return <LoadingState />;
  }

  if (error || !controller) {
    return (
      <PageLayout>
        <div className="p-6">
          <div className="rounded-md bg-red-50 p-4 dark:bg-red-900/20">
            <div className="flex">
              <ExclamationCircleIcon className="h-5 w-5 text-red-400" aria-hidden="true" />
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                  Controller not found
                </h3>
                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                  <p>No controller found with ID: {controllerId}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </PageLayout>
    );
  }

  // Prepare InfoCard items for Controller Info section
  const controllerInfoItems = [
    { label: 'ID', value: controller.id, mono: true, 'data-testid': `controller-id-${controller.id}` },
    { label: 'Address', value: controller.address, 'data-testid': `controller-address-${controller.id}` },
    { label: 'Version', value: controller.version },
      {
        label: 'First Seen',
        value: controller.first_seen ? formatRelativeTime(controller.first_seen) : 'Never',
      },
      {
        label: 'Last Seen',
        value: controller.last_seen ? formatRelativeTime(controller.last_seen) : 'Never',
      },
  ];

  // Prepare InfoCard items for System Info section
  const systemInfoItems = [
    { label: 'Platform', value: controller.platform },
    { label: 'Python', value: controller.python_version },
    { label: 'Memory', value: controller.memory_mb ? `${controller.memory_mb} MB` : null },
    { label: 'CPU Cores', value: controller.cpu_count },
  ];

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
              <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100" data-testid={`controller-name-${controller.id}`}>
                {controller.name}
              </h1>
              <StatusBadge status={displayStatus} showIcon data-testid={`controller-status-${controller.id}`} />
            </div>
            {controller.description && (
              <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                {controller.description}
              </p>
            )}
          </div>
        </div>

        {/* Info Cards Grid */}
        <div className="grid gap-6 md:grid-cols-2">
          <InfoCard
            title="Controller Info"
            items={controllerInfoItems}
            data-testid={`controller-info-${controller.id}`}
          />
          <InfoCard
            title="System Info"
            items={systemInfoItems}
            data-testid={`controller-system-info-${controller.id}`}
          />
        </div>

        {/* Assigned Trains Section */}
        <section>
          <h2 className="mb-4 text-xl font-semibold text-gray-900 dark:text-gray-100">
            Assigned Trains
          </h2>
          <AssignedTrainsTable
            trains={controller.trains ?? []}
            controllerId={controller.id}
            controllerName={controller.name}
          />
        </section>
      </div>
    </PageLayout>
  );
};

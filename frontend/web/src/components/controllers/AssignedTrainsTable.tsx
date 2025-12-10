import React from 'react';
import { Link } from 'react-router-dom';
import { EmptyState } from '@/components/common/EmptyState';
import { Train } from '@/api/types';
import { CubeIcon } from '@heroicons/react/24/outline';

export interface AssignedTrainsTableProps {
  /** Array of trains assigned to this controller */
  trains: Train[];
  /** Controller ID for breadcrumb navigation context */
  controllerId: string;
  /** Controller name for breadcrumb display text */
  controllerName: string;
}

/**
 * Build a link to the train detail page with breadcrumb context.
 * Uses URLSearchParams for proper URL encoding of special characters.
 */
const buildTrainLink = (
  trainId: string,
  controllerId: string,
  controllerName: string
): string => {
  const params = new URLSearchParams({
    from: `/controllers/${controllerId}`,
    fromName: controllerName,
  });
  return `/trains/${trainId}?${params.toString()}`;
};

/**
 * Table component displaying trains assigned to a controller.
 * Each train row includes a link to the train detail page with
 * breadcrumb context for navigation back to the controller.
 *
 * @example
 * <AssignedTrainsTable
 *   trains={controller.trains}
 *   controllerId={controller.id}
 *   controllerName={controller.name}
 * />
 */
export const AssignedTrainsTable: React.FC<AssignedTrainsTableProps> = ({
  trains,
  controllerId,
  controllerName,
}) => {
  if (trains.length === 0) {
    return (
      <EmptyState
        title="No Trains Assigned"
        description="This controller has no trains assigned to it."
        icon={<CubeIcon className="h-12 w-12" />}
      />
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700" data-testid={`controller-trains-${controllerId}`}>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400"
              >
                Name
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400"
              >
                ID
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400"
              >
                Plugin
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400"
              >
                Model
              </th>
              <th
                scope="col"
                className="px-4 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400"
              >
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-900">
            {trains.map((train) => (
              <tr key={train.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                <td className="whitespace-nowrap px-4 py-3 text-sm font-medium text-gray-900 dark:text-gray-100">
                  {train.name}
                </td>
                <td className="whitespace-nowrap px-4 py-3 font-mono text-sm text-gray-500 dark:text-gray-400">
                  {train.id}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {train.plugin.name}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                  {train.model ?? '--'}
                </td>
                <td className="whitespace-nowrap px-4 py-3 text-sm">
                  <Link
                    to={buildTrainLink(train.id, controllerId, controllerName)}
                    className="font-medium text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

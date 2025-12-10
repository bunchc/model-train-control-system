import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { StatusBadge } from '@/components/common/StatusBadge';
import { EdgeController } from '@/api/types';
import { formatRelativeTime } from '@/utils/formatting';
import { calculateControllerStatus } from '@/utils/controllerStatus';

export interface ControllerCardProps {
  controller: EdgeController;
  onClick?: () => void;
}

/**
 * Controller card component for displaying edge controller status
 */
export const ControllerCard: React.FC<ControllerCardProps> = ({ controller, onClick }) => {
  // Calculate display status based on last_seen timestamp age
  const displayStatus = calculateControllerStatus(controller.last_seen);

  return (
    <Card
      className={onClick ? 'cursor-pointer transition-shadow hover:shadow-md' : ''}
      onClick={onClick}
      data-testid={`controller-card-${controller.id}`}
    >
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle data-testid={`controller-name-${controller.id}`}>{controller.name}</CardTitle>
            {controller.description && (
              <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                {controller.description}
              </p>
            )}
          </div>
          <StatusBadge status={displayStatus} showIcon data-testid={`controller-status-${controller.id}`} />
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-2">
          {/* Address */}
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Address:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100" data-testid={`controller-address-${controller.id}`}>
              {controller.address || '--'}
            </span>
          </div>

          {/* Version */}
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Version:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {controller.version || '--'}
            </span>
          </div>

          {/* First Seen */}
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">First Seen:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {controller.first_seen ? formatRelativeTime(controller.first_seen) : 'Never'}
            </span>
          </div>

          {/* Last Seen */}
          <div className="flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Last Seen:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {controller.last_seen ? formatRelativeTime(controller.last_seen) : 'Never'}
            </span>
          </div>

          {/* Train Count */}
          <div className="flex justify-between text-sm" data-testid={`controller-trains-${controller.id}`}>
            <span className="text-gray-600 dark:text-gray-400">Trains:</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {controller.trains?.length ?? 0}
            </span>
          </div>
        </div>

        {/* Platform info footer */}
        {(controller.platform || controller.python_version) && (
          <div className="mt-4 border-t border-gray-200 pt-3 dark:border-gray-700">
            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>{controller.platform || 'Unknown platform'}</span>
              {controller.python_version && <span>Python {controller.python_version}</span>}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

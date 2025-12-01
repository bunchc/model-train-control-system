import React from 'react';
import { Link } from 'react-router-dom';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { StatusBadge } from '@/components/common/StatusBadge';
import { SpeedGauge } from './SpeedGauge';
import { Train } from '@/api/types';
import { useTrainStatus } from '@/api/queries';

export interface TrainCardProps {
  train: Train;
}

/**
 * Train card component for dashboard grid
 */
export const TrainCard: React.FC<TrainCardProps> = ({ train }) => {
  const { data: status, isLoading } = useTrainStatus(train.id);

  return (
    <Link to={`/trains/${train.id}`} className="block">
      <Card className="transition-shadow hover:shadow-md">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle>{train.name}</CardTitle>
              {train.description && (
                <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{train.description}</p>
              )}
            </div>
            <StatusBadge status={status ? (status.speed > 0 ? 'running' : 'stopped') : 'offline'} />
          </div>
        </CardHeader>

        <CardContent>
          <div className="flex items-center justify-between">
            {/* Speed Gauge */}
            <div className="flex-shrink-0">
              <SpeedGauge speed={status?.speed ?? 0} size="md" />
            </div>

            {/* Telemetry */}
            <div className="ml-4 flex-1 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Voltage:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {status?.voltage.toFixed(2) ?? '--'}V
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Current:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {status?.current.toFixed(3) ?? '--'}A
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Position:</span>
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {status?.position ?? '--'}
                </span>
              </div>
            </div>
          </div>

          {/* Plugin info */}
          <div className="mt-4 border-t border-gray-200 pt-3 dark:border-gray-700">
            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>Plugin: {train.plugin.name}</span>
              <span>ID: {train.id}</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};

import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { SpeedGauge } from './SpeedGauge';
import { TrainStatus } from '@/api/types';
import { formatRelativeTime } from '@/utils/formatting';
import { ClockIcon, ArrowRightIcon, ArrowLeftIcon, InformationCircleIcon } from '@heroicons/react/24/outline';

export interface TelemetryDisplayProps {
  status: TrainStatus;
}

/**
 * Display real-time train telemetry data
 */
export const TelemetryDisplay: React.FC<TelemetryDisplayProps> = ({ status }) => {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Live Telemetry
          <div className="group relative">
            <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300" />
            <div className="absolute bottom-full left-1/2 mb-2 hidden w-48 -translate-x-1/2 transform rounded bg-gray-900 p-2 text-xs text-white group-hover:block dark:bg-gray-700">
              Real-time data from the train showing current operational status
            </div>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Speed Gauge */}
        <div className="flex justify-center">
          <SpeedGauge speed={status.speed} size="lg" />
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          <MetricCard
            label="Speed"
            value={`${status.speed}%`}
            tooltip="Current motor speed percentage from 0% (stopped) to 100% (maximum speed)"
          />
          <MetricCard
            label="Direction"
            value={status.direction === 'FORWARD' ? 'Forward' : 'Reverse'}
            icon={status.direction === 'FORWARD' ? ArrowRightIcon : ArrowLeftIcon}
            iconColor={status.direction === 'FORWARD' ? 'text-green-600 dark:text-green-400' : 'text-blue-600 dark:text-blue-400'}
            tooltip="Current movement direction: Forward or Reverse"
          />
        </div>

        {/* Last Updated */}
        {status.timestamp && (
          <div className="flex items-center justify-center gap-2 text-xs text-gray-500 dark:text-gray-400">
            <ClockIcon className="h-4 w-4" aria-hidden="true" />
            <span>Updated {formatRelativeTime(status.timestamp)}</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

interface MetricCardProps {
  label: string;
  value: string | number;
  colSpan?: number;
  icon?: React.ComponentType<{ className?: string }>;
  iconColor?: string;
  tooltip?: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, colSpan = 1, icon: Icon, iconColor, tooltip }) => {
  return (
    <div
      className={`rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900 ${
        colSpan === 2 ? 'col-span-2' : ''
      }`}
    >
      <div className="flex items-center gap-1 text-xs font-medium text-gray-600 dark:text-gray-400">
        {label}
        {tooltip && (
          <div className="group relative">
            <InformationCircleIcon className="h-3 w-3 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300" />
            <div className="absolute bottom-full left-1/2 mb-2 hidden w-48 -translate-x-1/2 transform rounded bg-gray-900 p-2 text-xs text-white group-hover:block dark:bg-gray-700 z-10">
              {tooltip}
            </div>
          </div>
        )}
      </div>
      <div className="mt-1 flex items-center gap-2">
        {Icon && <Icon className={`h-5 w-5 ${iconColor || 'text-gray-500'}`} aria-hidden="true" />}
        <div className="text-lg font-semibold text-gray-900 dark:text-gray-100">{value}</div>
      </div>
    </div>
  );
};

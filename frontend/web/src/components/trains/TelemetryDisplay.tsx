import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { SpeedGauge } from './SpeedGauge';
import { TrainStatus } from '@/api/types';
import { formatVoltage, formatCurrent, formatRelativeTime } from '@/utils/formatting';
import { ClockIcon } from '@heroicons/react/24/outline';

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
        <CardTitle>Live Telemetry</CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Speed Gauge */}
        <div className="flex justify-center">
          <SpeedGauge speed={status.speed} size="lg" />
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-4">
          <MetricCard label="Voltage" value={formatVoltage(status.voltage)} />
          <MetricCard label="Current" value={formatCurrent(status.current)} />
          <MetricCard label="Position" value={status.position} colSpan={2} />
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
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, colSpan = 1 }) => {
  return (
    <div
      className={`rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900 ${
        colSpan === 2 ? 'col-span-2' : ''
      }`}
    >
      <div className="text-xs font-medium text-gray-600 dark:text-gray-400">{label}</div>
      <div className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">{value}</div>
    </div>
  );
};

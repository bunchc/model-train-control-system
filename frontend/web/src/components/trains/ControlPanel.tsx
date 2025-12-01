import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { useSendCommand } from '@/api/queries';
import { TrainCommand } from '@/api/types';
import { SPEED_LIMITS } from '@/utils/constants';
import toast from 'react-hot-toast';
import {
  PlayIcon,
  StopIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

export interface ControlPanelProps {
  trainId: string;
  currentSpeed: number;
  isOnline: boolean;
}

/**
 * Train control panel with speed, direction, and emergency stop
 */
export const ControlPanel: React.FC<ControlPanelProps> = ({ trainId, currentSpeed, isOnline }) => {
  const [speed, setSpeed] = useState(currentSpeed);
  const { mutate: sendCommand, isPending } = useSendCommand();

  const handleCommand = (command: TrainCommand, successMessage: string) => {
    sendCommand(
      { trainId, command },
      {
        onSuccess: () => {
          toast.success(successMessage);
        },
        onError: (error) => {
          toast.error(`Command failed: ${error.message}`);
        },
      }
    );
  };

  const handleSpeedChange = (newSpeed: number) => {
    setSpeed(newSpeed);
  };

  const handleSetSpeed = () => {
    handleCommand({ action: 'setSpeed', speed }, `Speed set to ${speed}%`);
  };

  const handleStart = () => {
    handleCommand({ action: 'start' }, 'Train started');
  };

  const handleStop = () => {
    handleCommand({ action: 'stop' }, 'Train stopped');
  };

  const handleForward = () => {
    handleCommand({ action: 'forward', direction: 'forward' }, 'Direction set to forward');
  };

  const handleReverse = () => {
    handleCommand({ action: 'reverse', direction: 'reverse' }, 'Direction set to reverse');
  };

  const handleEmergencyStop = () => {
    if (confirm('Are you sure you want to emergency stop the train?')) {
      handleCommand({ action: 'stop' }, 'Emergency stop activated');
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Control Panel</CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Speed Control */}
        <div>
          <label htmlFor="speed-slider" className="mb-2 block text-sm font-medium text-gray-700 dark:text-gray-300">
            Speed: {speed}%
          </label>
          <input
            id="speed-slider"
            type="range"
            min={SPEED_LIMITS.MIN}
            max={SPEED_LIMITS.MAX}
            value={speed}
            onChange={(e) => handleSpeedChange(Number(e.target.value))}
            disabled={!isOnline || isPending}
            className="h-2 w-full cursor-pointer appearance-none rounded-lg bg-gray-200 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-gray-700"
            aria-label="Speed control slider"
          />
          <div className="mt-2 flex justify-between text-xs text-gray-500 dark:text-gray-400">
            <span>0%</span>
            <span>50%</span>
            <span>100%</span>
          </div>
          <Button
            onClick={handleSetSpeed}
            disabled={!isOnline || isPending || speed === currentSpeed}
            isLoading={isPending}
            className="mt-3 w-full"
          >
            Apply Speed
          </Button>
        </div>

        {/* Primary Controls */}
        <div className="grid grid-cols-2 gap-3">
          <Button
            onClick={handleStart}
            disabled={!isOnline || isPending}
            isLoading={isPending}
            variant="primary"
            className="w-full"
          >
            <PlayIcon className="mr-2 h-5 w-5" aria-hidden="true" />
            Start
          </Button>
          <Button
            onClick={handleStop}
            disabled={!isOnline || isPending}
            isLoading={isPending}
            variant="secondary"
            className="w-full"
          >
            <StopIcon className="mr-2 h-5 w-5" aria-hidden="true" />
            Stop
          </Button>
        </div>

        {/* Direction Controls */}
        <div className="grid grid-cols-2 gap-3">
          <Button
            onClick={handleForward}
            disabled={!isOnline || isPending}
            isLoading={isPending}
            variant="secondary"
            className="w-full"
          >
            <ArrowUpIcon className="mr-2 h-5 w-5" aria-hidden="true" />
            Forward
          </Button>
          <Button
            onClick={handleReverse}
            disabled={!isOnline || isPending}
            isLoading={isPending}
            variant="secondary"
            className="w-full"
          >
            <ArrowDownIcon className="mr-2 h-5 w-5" aria-hidden="true" />
            Reverse
          </Button>
        </div>

        {/* Emergency Stop */}
        <div className="border-t border-gray-200 pt-4 dark:border-gray-700">
          <Button
            onClick={handleEmergencyStop}
            disabled={!isOnline || isPending}
            isLoading={isPending}
            variant="danger"
            size="lg"
            className="w-full"
          >
            <ExclamationTriangleIcon className="mr-2 h-5 w-5" aria-hidden="true" />
            Emergency Stop
          </Button>
        </div>

        {/* Status */}
        {!isOnline && (
          <div className="rounded-md bg-yellow-50 p-3 dark:bg-yellow-900/20">
            <p className="text-sm text-yellow-800 dark:text-yellow-300">
              Train is offline. Controls are disabled.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

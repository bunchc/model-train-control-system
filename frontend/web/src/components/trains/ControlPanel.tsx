import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/Card';
import { useSendCommand } from '@/api/queries';
import { TrainCommand } from '@/api/types';
import { SPEED_LIMITS } from '@/utils/constants';
import toast from 'react-hot-toast';
import {
  PlayIcon,
  StopIcon,
  ArrowRightIcon,
  ArrowLeftIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
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
  const [direction, setDirection] = useState<'forward' | 'reverse'>('forward');
  const { mutate: sendCommand, isPending } = useSendCommand();

  // Sync local speed with current speed when it changes
  useEffect(() => {
    setSpeed(currentSpeed);
  }, [currentSpeed]);

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

  const handleDirectionChange = (newDirection: 'forward' | 'reverse') => {
    setDirection(newDirection);
  };

  const handleApplySettings = () => {
    // Send direction first, then speed
    handleCommand(
      { action: direction, direction },
      `Direction set to ${direction}`
    );

    // Small delay to ensure direction is set before speed
    setTimeout(() => {
      handleCommand({ action: 'setSpeed', speed }, `Speed set to ${speed}%`);
    }, 100);
  };

  const handleStart = () => {
    handleCommand({ action: 'start' }, 'Train started');
  };

  const handleStop = () => {
    // Gradual stop using setSpeed to 0 (will use speed ramping)
    handleCommand({ action: 'setSpeed', speed: 0 }, 'Train stopping gradually');
    setSpeed(0); // Reset speed display when stopping
  };

  const handleEmergencyStop = () => {
    if (confirm('EMERGENCY STOP: This will immediately cut power to the motor. Are you sure?')) {
      handleCommand({ action: 'emergencyStop' }, 'Emergency stop activated - motor stopped immediately');
      setSpeed(0); // Reset speed display
    }
  };

  const hasChanges = speed !== currentSpeed;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Control Panel
          <div className="group relative">
            <InformationCircleIcon className="h-4 w-4 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300" />
            <div className="absolute bottom-full left-1/2 mb-2 hidden w-64 -translate-x-1/2 transform rounded bg-gray-900 p-2 text-xs text-white group-hover:block dark:bg-gray-700 z-10">
              Configure train settings, then apply changes. Start/Stop and Emergency controls are immediate.
            </div>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Configuration Section */}
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4 dark:border-blue-800 dark:bg-blue-900/20">
          <h3 className="mb-4 text-sm font-semibold text-blue-900 dark:text-blue-100">Train Configuration</h3>

          {/* Speed Control */}
          <div className="mb-4">
            <div className="mb-2 flex items-center gap-2">
              <label htmlFor="speed-slider" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Speed: {speed}%
              </label>
              <div className="group relative">
                <InformationCircleIcon className="h-3 w-3 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300" />
                <div className="absolute bottom-full left-1/2 mb-2 hidden w-48 -translate-x-1/2 transform rounded bg-gray-900 p-2 text-xs text-white group-hover:block dark:bg-gray-700 z-10">
                  Set desired speed from 0% (stopped) to 100% (maximum)
                </div>
              </div>
            </div>
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
            <div className="mt-1 flex justify-between text-xs text-gray-500 dark:text-gray-400">
              <span>0%</span>
              <span>50%</span>
              <span>100%</span>
            </div>
          </div>

          {/* Direction Control */}
          <div className="mb-4">
            <div className="mb-2 flex items-center gap-2">
              <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Direction:</label>
              <div className="group relative">
                <InformationCircleIcon className="h-3 w-3 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300" />
                <div className="absolute bottom-full left-1/2 mb-2 hidden w-48 -translate-x-1/2 transform rounded bg-gray-900 p-2 text-xs text-white group-hover:block dark:bg-gray-700 z-10">
                  Choose movement direction: Forward or Reverse
                </div>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <Button
                onClick={() => handleDirectionChange('forward')}
                variant={direction === 'forward' ? 'primary' : 'secondary'}
                className="w-full"
                disabled={!isOnline || isPending}
              >
                <ArrowRightIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                Forward
              </Button>
              <Button
                onClick={() => handleDirectionChange('reverse')}
                variant={direction === 'reverse' ? 'primary' : 'secondary'}
                className="w-full"
                disabled={!isOnline || isPending}
              >
                <ArrowLeftIcon className="mr-2 h-4 w-4" aria-hidden="true" />
                Reverse
              </Button>
            </div>
          </div>

          {/* Apply Configuration */}
          <Button
            onClick={handleApplySettings}
            disabled={!isOnline || isPending || !hasChanges}
            isLoading={isPending}
            variant="primary"
            className="w-full"
          >
            Apply Configuration
            {hasChanges && <span className="ml-1 text-xs">●</span>}
          </Button>
        </div>

        {/* Immediate Controls Section */}
        <div>
          <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">Immediate Controls</h3>
          <div className="grid grid-cols-2 gap-3">
            <div className="group relative">
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
              <div className="absolute bottom-full left-1/2 mb-2 hidden w-48 -translate-x-1/2 transform rounded bg-gray-900 p-2 text-xs text-white group-hover:block dark:bg-gray-700 z-10">
                Start the motor with current configuration
              </div>
            </div>
            <div className="group relative">
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
              <div className="absolute bottom-full left-1/2 mb-2 hidden w-48 -translate-x-1/2 transform rounded bg-gray-900 p-2 text-xs text-white group-hover:block dark:bg-gray-700 z-10">
                Gradually reduce speed to zero using 3-second speed ramping
              </div>
            </div>
          </div>
        </div>

        {/* Emergency Stop */}
        <div className="border-t border-gray-200 pt-4 dark:border-gray-700">
          <div className="group relative">
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
            <div className="absolute bottom-full left-1/2 mb-2 hidden w-56 -translate-x-1/2 transform rounded bg-gray-900 p-2 text-xs text-white group-hover:block dark:bg-gray-700 z-10">
              ⚠️ IMMEDIATE motor stop - bypasses gradual speed reduction. Use only in emergencies.
            </div>
          </div>
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

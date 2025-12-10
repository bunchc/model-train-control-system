import React from 'react';
import { cn } from '@/utils/cn';
import {
  CheckCircleIcon,
  XCircleIcon,
  QuestionMarkCircleIcon,
  ExclamationCircleIcon,
  StopCircleIcon,
  PlayCircleIcon,
} from '@heroicons/react/16/solid';

export interface StatusBadgeProps {
  status: 'online' | 'offline' | 'error' | 'running' | 'stopped' | 'unknown';
  className?: string;
  /** Show icon instead of dot indicator */
  showIcon?: boolean;
}

/**
 * Status badge with predefined colors for common states
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  className,
    showIcon = false,
    ...props
}) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'online':
        return {
          color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
          label: 'Online',
          dot: 'bg-green-500',
          icon: CheckCircleIcon,
          iconColor: 'text-green-500',
        };
      case 'running':
        return {
          color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
          label: 'Running',
          dot: 'bg-green-500',
          icon: PlayCircleIcon,
          iconColor: 'text-green-500',
        };
      case 'offline':
        return {
          color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
          label: 'Offline',
          dot: 'bg-gray-500',
          icon: XCircleIcon,
          iconColor: 'text-gray-500',
        };
      case 'stopped':
        return {
          color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
          label: 'Stopped',
          dot: 'bg-gray-500',
          icon: StopCircleIcon,
          iconColor: 'text-gray-500',
        };
      case 'error':
        return {
          color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
          label: 'Error',
          dot: 'bg-red-500',
          icon: ExclamationCircleIcon,
          iconColor: 'text-red-500',
        };
      case 'unknown':
        return {
          color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-300',
          label: 'Unknown',
          dot: 'bg-yellow-500',
          icon: QuestionMarkCircleIcon,
          iconColor: 'text-yellow-500',
        };
      default:
        return {
          color: 'bg-gray-100 text-gray-800',
          label: status,
          dot: 'bg-gray-500',
          icon: QuestionMarkCircleIcon,
          iconColor: 'text-gray-500',
        };
    }
  };

  const { color, label, dot, icon: Icon, iconColor } = getStatusConfig();

  // Allow passing data-testid prop
  const dataTestId = (props as any)["data-testid"];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        color,
        className
      )}
      data-testid={dataTestId}
    >
      {showIcon ? (
        <Icon className={cn('h-3.5 w-3.5', iconColor)} aria-hidden="true" />
      ) : (
        <span className={cn('h-1.5 w-1.5 rounded-full', dot)} aria-hidden="true" />
      )}
      {label}
    </span>
  );
};

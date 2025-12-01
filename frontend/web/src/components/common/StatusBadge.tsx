import React from 'react';
import { cn } from '@/utils/cn';

export interface StatusBadgeProps {
  status: 'online' | 'offline' | 'error' | 'running' | 'stopped';
  className?: string;
}

/**
 * Status badge with predefined colors for common states
 */
export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, className }) => {
  const getStatusConfig = () => {
    switch (status) {
      case 'online':
      case 'running':
        return {
          color: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300',
          label: status === 'online' ? 'Online' : 'Running',
          dot: 'bg-green-500',
        };
      case 'offline':
      case 'stopped':
        return {
          color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
          label: status === 'offline' ? 'Offline' : 'Stopped',
          dot: 'bg-gray-500',
        };
      case 'error':
        return {
          color: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300',
          label: 'Error',
          dot: 'bg-red-500',
        };
      default:
        return {
          color: 'bg-gray-100 text-gray-800',
          label: status,
          dot: 'bg-gray-500',
        };
    }
  };

  const { color, label, dot } = getStatusConfig();

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium',
        color,
        className
      )}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', dot)} aria-hidden="true" />
      {label}
    </span>
  );
};

import { formatDistanceToNow } from 'date-fns';

/**
 * Format speed value with unit
 */
export const formatSpeed = (speed: number): string => {
  return `${speed}%`;
};

/**
 * Format timestamp as relative time
 */
export const formatRelativeTime = (timestamp: string | Date): string => {
  return formatDistanceToNow(new Date(timestamp), { addSuffix: true });
};

/**
 * Get color class for speed value
 */
export const getSpeedColor = (speed: number): string => {
  if (speed === 0) return 'text-gray-500';
  if (speed < 30) return 'text-green-500';
  if (speed < 70) return 'text-yellow-500';
  return 'text-red-500';
};

/**
 * Get status badge color
 */
export const getStatusColor = (status: 'online' | 'offline' | 'error'): string => {
  switch (status) {
    case 'online':
      return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-300';
    case 'offline':
      return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    case 'error':
      return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-300';
    default:
      return 'bg-gray-100 text-gray-800';
  }
};

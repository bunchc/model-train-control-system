import { format } from 'date-fns';

// Toggle time formatting debug logs
const DEBUG_TIME_FORMATTING = false;

/**
 * Format speed value with unit
 */
export const formatSpeed = (speed: number): string => {
  return `${speed}%`;
};

/**
 * Format timestamp as relative time
 */
export const formatRelativeTime = (timestamp: string | Date | null | undefined): string => {
  if (!timestamp) return 'Never';
  let date: Date;
  try {
    if (typeof timestamp === 'string') {
      // If format is 'YYYY-MM-DD HH:MM:SS', parse as local time
      if (/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(timestamp)) {
        const [datePart, timePart] = timestamp.split(' ');
        const [year, month, day] = datePart.split('-').map(Number);
        const [hour, minute, second] = timePart.split(':').map(Number);
        // Parse as UTC (GMT) since backend sends in GMT
        date = new Date(Date.UTC(year, month - 1, day, hour, minute, second));
        if (DEBUG_TIME_FORMATTING) {
          // eslint-disable-next-line no-console
          console.debug('[formatRelativeTime][utc branch] input:', timestamp, 'parsed local:', date.toString(), 'UTC:', date.toISOString());
        }
      } else {
        // Fallback: try native parsing (handles ISO8601, etc)
        date = new Date(timestamp);
        if (DEBUG_TIME_FORMATTING) {
          // eslint-disable-next-line no-console
          console.debug('[formatRelativeTime][native branch] input:', timestamp, 'parsed local:', date.toString(), 'UTC:', date.toISOString());
        }
      }
    } else if (timestamp instanceof Date) {
      date = timestamp;
      if (DEBUG_TIME_FORMATTING) {
        // eslint-disable-next-line no-console
        console.debug('[formatRelativeTime][Date branch] input:', timestamp, 'parsed local:', date.toString(), 'UTC:', date.toISOString());
      }
    } else {
      // Defensive fallback
      throw new Error('Invalid timestamp type');
    }
    if (isNaN(date.getTime())) {
      if (DEBUG_TIME_FORMATTING) {
        // eslint-disable-next-line no-console
        console.warn('[formatRelativeTime] Invalid date:', timestamp);
      }
      return 'Never';
    }
  } catch (err) {
    if (DEBUG_TIME_FORMATTING) {
      // eslint-disable-next-line no-console
      console.error('[formatRelativeTime] Exception:', err, 'timestamp:', timestamp);
    }
    return 'Never';
  }
  const now = new Date();
  if (DEBUG_TIME_FORMATTING) {
    // Log both local and UTC for now
    // eslint-disable-next-line no-console
    console.debug('[formatRelativeTime] now local:', now.toString(), 'UTC:', now.toISOString());
  }
  const diffMs = now.getTime() - date.getTime();
  if (DEBUG_TIME_FORMATTING) {
    // eslint-disable-next-line no-console
    console.debug('[formatRelativeTime] diffMs:', diffMs);
  }
  if (diffMs < 0) return 'Never'; // Future timestamp
  if (diffMs < 60 * 1000) return 'Just now';
  // Format as YYYY-MM-DD HH:mm in local time
  return format(date, 'yyyy-MM-dd HH:mm');
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

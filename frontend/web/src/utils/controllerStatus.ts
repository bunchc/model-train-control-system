/**
 * Controller status calculation based on last_seen timestamp
 *
 * Thresholds are configurable constants that determine when a controller
 * transitions between online → unknown → offline states.
 */

/** Configurable thresholds in seconds */
export const CONTROLLER_STATUS_THRESHOLDS = {
  /** Maximum age (seconds) to be considered online */
  ONLINE_MAX_AGE: 30,
  /** Maximum age (seconds) to be considered unknown (stale but recent) */
  UNKNOWN_MAX_AGE: 120,
} as const;

export type CalculatedControllerStatus = 'online' | 'unknown' | 'offline';

/**
 * Calculate controller display status based on last_seen timestamp age.
 *
 * @param lastSeen - ISO timestamp string, null, or undefined
 * @returns 'online' if recent, 'unknown' if stale, 'offline' if old or missing
 *
 * @example
 * calculateControllerStatus('2025-12-04T16:00:00Z') // depends on current time
 * calculateControllerStatus(null) // 'offline'
 */
export const calculateControllerStatus = (
  lastSeen: string | null | undefined
): CalculatedControllerStatus => {
  if (!lastSeen) {
    return 'offline';
  }

  try {
    const lastSeenDate = new Date(lastSeen);

    // Check for invalid date
    if (isNaN(lastSeenDate.getTime())) {
      return 'offline';
    }

    const ageSeconds = (Date.now() - lastSeenDate.getTime()) / 1000;

    // Handle future timestamps (clock skew) - treat as online
    if (ageSeconds < 0) {
      return 'online';
    }

    if (ageSeconds < CONTROLLER_STATUS_THRESHOLDS.ONLINE_MAX_AGE) {
      return 'online';
    }

    if (ageSeconds < CONTROLLER_STATUS_THRESHOLDS.UNKNOWN_MAX_AGE) {
      return 'unknown';
    }

    return 'offline';
  } catch {
    return 'offline';
  }
};

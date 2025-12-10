import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  calculateControllerStatus,
  CONTROLLER_STATUS_THRESHOLDS,
} from '@/utils/controllerStatus';

describe('controllerStatus', () => {
  describe('calculateControllerStatus', () => {
    const NOW = new Date('2025-12-04T16:00:00.000Z').getTime();

    beforeEach(() => {
      vi.useFakeTimers();
      vi.setSystemTime(NOW);
    });

    afterEach(() => {
      vi.useRealTimers();
    });

    it('returns "online" for timestamp less than 30 seconds ago', () => {
      // 10 seconds ago
      const timestamp = new Date(NOW - 10 * 1000).toISOString();
      expect(calculateControllerStatus(timestamp)).toBe('online');
    });

    it('returns "online" for timestamp exactly at online threshold boundary', () => {
      // Exactly 29 seconds ago (just under 30s threshold)
      const timestamp = new Date(
        NOW - (CONTROLLER_STATUS_THRESHOLDS.ONLINE_MAX_AGE - 1) * 1000
      ).toISOString();
      expect(calculateControllerStatus(timestamp)).toBe('online');
    });

    it('returns "unknown" for timestamp between 30-120 seconds ago', () => {
      // 60 seconds ago
      const timestamp = new Date(NOW - 60 * 1000).toISOString();
      expect(calculateControllerStatus(timestamp)).toBe('unknown');
    });

    it('returns "unknown" for timestamp exactly at online threshold', () => {
      // Exactly 30 seconds ago (at the online threshold)
      const timestamp = new Date(
        NOW - CONTROLLER_STATUS_THRESHOLDS.ONLINE_MAX_AGE * 1000
      ).toISOString();
      expect(calculateControllerStatus(timestamp)).toBe('unknown');
    });

    it('returns "unknown" for timestamp just under unknown threshold', () => {
      // 119 seconds ago (just under 120s threshold)
      const timestamp = new Date(
        NOW - (CONTROLLER_STATUS_THRESHOLDS.UNKNOWN_MAX_AGE - 1) * 1000
      ).toISOString();
      expect(calculateControllerStatus(timestamp)).toBe('unknown');
    });

    it('returns "offline" for timestamp older than 120 seconds', () => {
      // 5 minutes ago
      const timestamp = new Date(NOW - 5 * 60 * 1000).toISOString();
      expect(calculateControllerStatus(timestamp)).toBe('offline');
    });

    it('returns "offline" for timestamp exactly at unknown threshold', () => {
      // Exactly 120 seconds ago (at the unknown threshold)
      const timestamp = new Date(
        NOW - CONTROLLER_STATUS_THRESHOLDS.UNKNOWN_MAX_AGE * 1000
      ).toISOString();
      expect(calculateControllerStatus(timestamp)).toBe('offline');
    });

    it('returns "offline" for null timestamp', () => {
      expect(calculateControllerStatus(null)).toBe('offline');
    });

    it('returns "offline" for undefined timestamp', () => {
      expect(calculateControllerStatus(undefined)).toBe('offline');
    });

    it('returns "offline" for invalid date string', () => {
      expect(calculateControllerStatus('not-a-date')).toBe('offline');
    });

    it('returns "offline" for empty string', () => {
      expect(calculateControllerStatus('')).toBe('offline');
    });

    it('returns "online" for future timestamp (clock skew)', () => {
      // 10 seconds in the future
      const timestamp = new Date(NOW + 10 * 1000).toISOString();
      expect(calculateControllerStatus(timestamp)).toBe('online');
    });

    it('handles various valid ISO timestamp formats', () => {
      // Standard ISO format
      const iso = new Date(NOW - 10 * 1000).toISOString();
      expect(calculateControllerStatus(iso)).toBe('online');

      // Without milliseconds
      const noMillis = '2025-12-04T15:59:50Z';
      vi.setSystemTime(new Date('2025-12-04T16:00:00Z'));
      expect(calculateControllerStatus(noMillis)).toBe('online');
    });
  });

  describe('CONTROLLER_STATUS_THRESHOLDS', () => {
    it('has expected default values', () => {
      expect(CONTROLLER_STATUS_THRESHOLDS.ONLINE_MAX_AGE).toBe(30);
      expect(CONTROLLER_STATUS_THRESHOLDS.UNKNOWN_MAX_AGE).toBe(120);
    });

    it('unknown threshold is greater than online threshold', () => {
      expect(CONTROLLER_STATUS_THRESHOLDS.UNKNOWN_MAX_AGE).toBeGreaterThan(
        CONTROLLER_STATUS_THRESHOLDS.ONLINE_MAX_AGE
      );
    });
  });
});

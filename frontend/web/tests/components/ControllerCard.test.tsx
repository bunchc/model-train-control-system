import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from '../utils/test-utils';
import { ControllerCard } from '@/components/controllers/ControllerCard';
import { EdgeController } from '@/api/types';

// Helper to create mock controller data
const createMockController = (
  overrides: Partial<EdgeController> = {}
): EdgeController => ({
  id: 'ctrl-123',
  name: 'Test Controller',
  description: 'A test controller',
  address: '192.168.1.100',
  trains: [],
  first_seen: '2025-12-04T12:00:00Z',
  last_seen: '2025-12-04T16:00:00Z',
  config_hash: 'abc123',
  version: '1.2.3',
  platform: 'Linux-5.15.0-aarch64',
  python_version: '3.11.2',
  memory_mb: 4096,
  cpu_count: 4,
  status: 'online',
  ...overrides,
});

describe('ControllerCard', () => {
  const NOW = new Date('2025-12-04T16:00:00.000Z').getTime();

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Basic Rendering', () => {
    it('renders controller name', () => {
      const controller = createMockController({ name: 'Pi Controller Alpha' });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Pi Controller Alpha')).toBeInTheDocument();
    });

    it('renders controller description when provided', () => {
      const controller = createMockController({
        description: 'Main layout controller',
      });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Main layout controller')).toBeInTheDocument();
    });

    it('does not render description element when not provided', () => {
      const controller = createMockController({ description: undefined });
      render(<ControllerCard controller={controller} />);

      // Name should exist, but description paragraph should not
      expect(screen.getByText('Test Controller')).toBeInTheDocument();
      expect(screen.queryByText('A test controller')).not.toBeInTheDocument();
    });

    it('displays controller address', () => {
      const controller = createMockController({ address: '10.0.0.50' });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('10.0.0.50')).toBeInTheDocument();
    });

    it('displays "--" when address is not available', () => {
      const controller = createMockController({ address: undefined });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('--')).toBeInTheDocument();
    });

    it('displays controller version', () => {
      const controller = createMockController({ version: '2.0.0-beta' });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('2.0.0-beta')).toBeInTheDocument();
    });

    it('displays "--" when version is not available', () => {
      const controller = createMockController({ version: undefined });
      render(<ControllerCard controller={controller} />);

      // Should have multiple "--" for missing data
      const dashes = screen.getAllByText('--');
      expect(dashes.length).toBeGreaterThan(0);
    });
  });

  describe('Status Badge', () => {
    it('shows "Online" when last_seen is within 30 seconds', () => {
      // 10 seconds ago
      const controller = createMockController({
        last_seen: new Date(NOW - 10 * 1000).toISOString(),
      });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Online')).toBeInTheDocument();
    });

    it('shows "Unknown" when last_seen is between 30-120 seconds ago', () => {
      // 60 seconds ago
      const controller = createMockController({
        last_seen: new Date(NOW - 60 * 1000).toISOString(),
      });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });

    it('shows "Offline" when last_seen is older than 120 seconds', () => {
      // 5 minutes ago
      const controller = createMockController({
        last_seen: new Date(NOW - 5 * 60 * 1000).toISOString(),
      });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Offline')).toBeInTheDocument();
    });

    it('shows "Offline" when last_seen is null', () => {
      const controller = createMockController({ last_seen: null });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Offline')).toBeInTheDocument();
    });

    it('shows "Offline" when last_seen is undefined', () => {
      const controller = createMockController({ last_seen: undefined });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  describe('Last Seen Display', () => {
    it('displays relative time for last_seen', () => {
      // 10 seconds ago should show "less than a minute ago" or similar
      const controller = createMockController({
        last_seen: new Date(NOW - 10 * 1000).toISOString(),
      });
      render(<ControllerCard controller={controller} />);

      // date-fns formatDistanceToNow should produce something like "less than a minute ago"
      expect(screen.getByText(/less than a minute ago/i)).toBeInTheDocument();
    });

    it('displays "Never" when last_seen is null', () => {
      const controller = createMockController({ last_seen: null });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Never')).toBeInTheDocument();
    });

    it('displays "Never" when last_seen is undefined', () => {
      const controller = createMockController({ last_seen: undefined });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Never')).toBeInTheDocument();
    });
  });

  describe('Train Count', () => {
    it('displays train count when trains array is provided', () => {
      const controller = createMockController({
        trains: [
          { id: 't1', name: 'Train 1' },
          { id: 't2', name: 'Train 2' },
        ] as EdgeController['trains'],
      });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('2')).toBeInTheDocument();
    });

    it('displays 0 when trains array is empty', () => {
      const controller = createMockController({ trains: [] });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });

    it('displays 0 when trains is undefined', () => {
      const controller = createMockController({ trains: undefined });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  describe('Platform Info Footer', () => {
    it('displays platform info when available', () => {
      const controller = createMockController({
        platform: 'Linux-6.1.0-rpi-arm64',
      });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Linux-6.1.0-rpi-arm64')).toBeInTheDocument();
    });

    it('displays Python version when available', () => {
      const controller = createMockController({ python_version: '3.12.0' });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Python 3.12.0')).toBeInTheDocument();
    });

    it('displays both platform and Python version', () => {
      const controller = createMockController({
        platform: 'Darwin-23.0.0',
        python_version: '3.11.5',
      });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Darwin-23.0.0')).toBeInTheDocument();
      expect(screen.getByText('Python 3.11.5')).toBeInTheDocument();
    });

    it('does not render footer when platform and python_version are both undefined', () => {
      const controller = createMockController({
        platform: undefined,
        python_version: undefined,
      });
      render(<ControllerCard controller={controller} />);

      // Footer should not be present - check that "Python" text doesn't appear
      expect(screen.queryByText(/Python/)).not.toBeInTheDocument();
      expect(screen.queryByText('Unknown platform')).not.toBeInTheDocument();
    });

    it('displays "Unknown platform" when only python_version is available', () => {
      const controller = createMockController({
        platform: undefined,
        python_version: '3.10.0',
      });
      render(<ControllerCard controller={controller} />);

      expect(screen.getByText('Unknown platform')).toBeInTheDocument();
      expect(screen.getByText('Python 3.10.0')).toBeInTheDocument();
    });
  });

  describe('Click Interaction', () => {
    it('calls onClick when card is clicked', async () => {
      // Use real timers for userEvent interaction tests
      vi.useRealTimers();
      const user = userEvent.setup();
      const handleClick = vi.fn();
      const controller = createMockController();

      render(<ControllerCard controller={controller} onClick={handleClick} />);

      // Click on the card (use the name as a reliable target)
      await user.click(screen.getByText('Test Controller'));

      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not error when clicked without onClick handler', async () => {
      // Use real timers for userEvent interaction tests
      vi.useRealTimers();
      const user = userEvent.setup();
      const controller = createMockController();

      render(<ControllerCard controller={controller} />);

      // Should not throw
      await user.click(screen.getByText('Test Controller'));
    });

    it('has cursor-pointer class when onClick is provided', () => {
      const controller = createMockController();
      const { container } = render(
        <ControllerCard controller={controller} onClick={() => {}} />
      );

      // The card should have cursor-pointer class
      const card = container.firstChild as HTMLElement;
      expect(card.className).toContain('cursor-pointer');
    });

    it('does not have cursor-pointer class when onClick is not provided', () => {
      const controller = createMockController();
      const { container } = render(<ControllerCard controller={controller} />);

      const card = container.firstChild as HTMLElement;
      expect(card.className).not.toContain('cursor-pointer');
    });
  });
});

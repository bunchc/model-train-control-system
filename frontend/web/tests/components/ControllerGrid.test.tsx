import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from '../utils/test-utils';
import { ControllerGrid } from '@/components/controllers/ControllerGrid';
import { EdgeController } from '@/api/types';

// Helper to create mock controller data
const createMockController = (
  id: string,
  name: string,
  overrides: Partial<EdgeController> = {}
): EdgeController => ({
  id,
  name,
  description: `Description for ${name}`,
  address: '192.168.1.100',
  trains: [],
  first_seen: '2025-12-04T12:00:00Z',
  last_seen: '2025-12-04T16:00:00Z',
  config_hash: 'abc123',
  version: '1.0.0',
  platform: 'Linux-5.15.0-aarch64',
  python_version: '3.11.2',
  memory_mb: 4096,
  cpu_count: 4,
  status: 'online',
  ...overrides,
});

describe('ControllerGrid', () => {
  const NOW = new Date('2025-12-04T16:00:00.000Z').getTime();

  beforeEach(() => {
    vi.useFakeTimers();
    vi.setSystemTime(NOW);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Empty State', () => {
    it('renders empty state when controllers array is empty', () => {
      render(<ControllerGrid controllers={[]} />);

      expect(screen.getByText('No controllers configured')).toBeInTheDocument();
    });

    it('renders helpful description in empty state', () => {
      render(<ControllerGrid controllers={[]} />);

      expect(
        screen.getByText(/Edge controllers will appear here/i)
      ).toBeInTheDocument();
    });

    it('renders ServerIcon in empty state', () => {
      const { container } = render(<ControllerGrid controllers={[]} />);

      // Check for the icon by looking for the SVG with expected classes
      const svg = container.querySelector('svg');
      expect(svg).toBeInTheDocument();
      expect(svg?.classList.contains('h-16')).toBe(true);
    });
  });

  describe('With Controllers', () => {
    it('renders a single controller card', () => {
      const controllers = [createMockController('ctrl-1', 'Alpha Controller')];

      render(<ControllerGrid controllers={controllers} />);

      expect(screen.getByText('Alpha Controller')).toBeInTheDocument();
    });

    it('renders multiple controller cards', () => {
      const controllers = [
        createMockController('ctrl-1', 'Alpha Controller'),
        createMockController('ctrl-2', 'Beta Controller'),
        createMockController('ctrl-3', 'Gamma Controller'),
      ];

      render(<ControllerGrid controllers={controllers} />);

      expect(screen.getByText('Alpha Controller')).toBeInTheDocument();
      expect(screen.getByText('Beta Controller')).toBeInTheDocument();
      expect(screen.getByText('Gamma Controller')).toBeInTheDocument();
    });

    it('renders correct number of controller cards', () => {
      const controllers = [
        createMockController('ctrl-1', 'Controller 1'),
        createMockController('ctrl-2', 'Controller 2'),
        createMockController('ctrl-3', 'Controller 3'),
        createMockController('ctrl-4', 'Controller 4'),
        createMockController('ctrl-5', 'Controller 5'),
      ];

      render(<ControllerGrid controllers={controllers} />);

      // Each controller should have its name rendered
      for (let i = 1; i <= 5; i++) {
        expect(screen.getByText(`Controller ${i}`)).toBeInTheDocument();
      }
    });

    it('does not show empty state when controllers exist', () => {
      const controllers = [createMockController('ctrl-1', 'Test Controller')];

      render(<ControllerGrid controllers={controllers} />);

      expect(
        screen.queryByText('No controllers configured')
      ).not.toBeInTheDocument();
    });
  });

  describe('Grid Layout', () => {
    it('applies grid classes for responsive layout', () => {
      const controllers = [
        createMockController('ctrl-1', 'Controller 1'),
        createMockController('ctrl-2', 'Controller 2'),
      ];

      const { container } = render(<ControllerGrid controllers={controllers} />);

      // Check for grid classes on the container
      const gridContainer = container.firstChild as HTMLElement;
      expect(gridContainer.classList.contains('grid')).toBe(true);
      expect(gridContainer.classList.contains('grid-cols-1')).toBe(true);
    });
  });

  describe('Controller Status Display', () => {
    it('shows online status for recently seen controllers', () => {
      const controllers = [
        createMockController('ctrl-1', 'Online Controller', {
          last_seen: new Date(NOW - 10 * 1000).toISOString(), // 10 seconds ago
        }),
      ];

      render(<ControllerGrid controllers={controllers} />);

      expect(screen.getByText('Online')).toBeInTheDocument();
    });

    it('shows unknown status for stale controllers', () => {
      const controllers = [
        createMockController('ctrl-1', 'Stale Controller', {
          last_seen: new Date(NOW - 60 * 1000).toISOString(), // 60 seconds ago
        }),
      ];

      render(<ControllerGrid controllers={controllers} />);

      expect(screen.getByText('Unknown')).toBeInTheDocument();
    });

    it('shows offline status for old controllers', () => {
      const controllers = [
        createMockController('ctrl-1', 'Offline Controller', {
          last_seen: new Date(NOW - 5 * 60 * 1000).toISOString(), // 5 minutes ago
        }),
      ];

      render(<ControllerGrid controllers={controllers} />);

      expect(screen.getByText('Offline')).toBeInTheDocument();
    });

    it('shows mixed statuses for multiple controllers', () => {
      const controllers = [
        createMockController('ctrl-1', 'Online Controller', {
          last_seen: new Date(NOW - 5 * 1000).toISOString(),
        }),
        createMockController('ctrl-2', 'Unknown Controller', {
          last_seen: new Date(NOW - 60 * 1000).toISOString(),
        }),
        createMockController('ctrl-3', 'Offline Controller', {
          last_seen: new Date(NOW - 300 * 1000).toISOString(),
        }),
      ];

      render(<ControllerGrid controllers={controllers} />);

      expect(screen.getByText('Online')).toBeInTheDocument();
      expect(screen.getByText('Unknown')).toBeInTheDocument();
      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  describe('Navigation', () => {
    it('navigates to controller detail page when card is clicked', async () => {
      vi.useRealTimers(); // userEvent requires real timers
      const user = userEvent.setup();

      const controllers = [createMockController('ctrl-123', 'Alpha Controller')];

      render(<ControllerGrid controllers={controllers} />);

      await user.click(screen.getByText('Alpha Controller'));

      // Verify URL changed to controller detail page
      expect(window.location.pathname).toBe('/controllers/ctrl-123');
    });

    it('constructs correct URL with controller ID', async () => {
      vi.useRealTimers();
      const user = userEvent.setup();

      const controllers = [
        createMockController('uuid-abc-123', 'Test Controller'),
      ];

      render(<ControllerGrid controllers={controllers} />);

      await user.click(screen.getByText('Test Controller'));

      expect(window.location.pathname).toBe('/controllers/uuid-abc-123');
    });

    it('each card navigates to its own controller detail page', async () => {
      vi.useRealTimers();
      const user = userEvent.setup();

      const controllers = [
        createMockController('ctrl-1', 'Controller One'),
        createMockController('ctrl-2', 'Controller Two'),
      ];

      const { unmount } = render(<ControllerGrid controllers={controllers} />);

      // Click first controller
      await user.click(screen.getByText('Controller One'));
      expect(window.location.pathname).toBe('/controllers/ctrl-1');

      // Clean up and reset URL for next test
      unmount();
      window.history.pushState({}, '', '/controllers');

      // Re-render and click second controller
      render(<ControllerGrid controllers={controllers} />);
      await user.click(screen.getByText('Controller Two'));
      expect(window.location.pathname).toBe('/controllers/ctrl-2');
    });
  });
});

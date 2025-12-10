import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ControllerDetail } from '@/pages/ControllerDetail';
import * as queries from '@/api/queries';

// Mock the API queries
vi.mock('@/api/queries', () => ({
  useController: vi.fn(),
}));

/**
 * Helper to render component with route parameters
 */
const renderWithRoute = (controllerId: string) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[`/controllers/${controllerId}`]}>
        <Routes>
          <Route path="/controllers/:controllerId" element={<ControllerDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('ControllerDetail', () => {
  // Mock localStorage and matchMedia for theme hook used by PageLayout/Header
  const localStorageMock = {
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
    length: 0,
    key: vi.fn(),
  };

  const matchMediaMock = vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));

  // Mock controller data with recent heartbeat (online)
  const mockController = {
    id: 'pi-001',
    name: 'Raspberry Pi Controller',
    description: 'Main layout controller',
    address: '192.168.1.100',
    enabled: true,
    version: '1.2.0',
    platform: 'Linux-armv7l',
    python_version: '3.11.2',
    memory_mb: 4096,
    cpu_count: 4,
    first_seen: '2024-01-15T10:00:00Z',
    last_seen: new Date().toISOString(), // Recent = online
    config_hash: 'abc123',
    trains: [
      {
        id: 'train-001',
        name: 'Test Express',
        description: 'A test train',
        model: 'HO Scale',
        plugin: { name: 'dc_motor_hat' },
      },
      {
        id: 'train-002',
        name: 'Freight Hauler',
        description: 'Freight train',
        model: 'N Scale',
        plugin: { name: 'pwm_gpio' },
      },
    ],
  };

  beforeEach(() => {
    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
    Object.defineProperty(window, 'matchMedia', {
      value: matchMediaMock,
      writable: true,
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('renders loading state while fetching', () => {
      vi.mocked(queries.useController).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
      } as any);

      renderWithRoute('pi-001');

      // LoadingState component has aria-live="polite" container
      const loadingContainer = screen.getByRole('status', { name: /loading/i });
      expect(loadingContainer).toBeInTheDocument();
    });
  });

  describe('Controller Not Found', () => {
    it('shows error state when controller not found', () => {
      vi.mocked(queries.useController).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Controller not found'),
      } as any);

      renderWithRoute('unknown-id');

      expect(screen.getByText(/controller not found/i)).toBeInTheDocument();
      expect(screen.getByText(/unknown-id/)).toBeInTheDocument();
    });
  });

  describe('Loaded State', () => {
    beforeEach(() => {
      vi.mocked(queries.useController).mockReturnValue({
        data: mockController,
        isLoading: false,
        error: null,
      } as any);
    });

    it('renders controller info when loaded', () => {
      renderWithRoute('pi-001');

      // Title and description should be visible
      expect(screen.getByRole('heading', { name: 'Raspberry Pi Controller' })).toBeInTheDocument();
      expect(screen.getByText('Main layout controller')).toBeInTheDocument();
    });

    it('shows controller info card with basic details', () => {
      renderWithRoute('pi-001');

      // Find the Controller Info section
      const infoCard = screen.getByRole('region', { name: /controller info/i });
      expect(within(infoCard).getByText('pi-001')).toBeInTheDocument();
      expect(within(infoCard).getByText('192.168.1.100')).toBeInTheDocument();
      expect(within(infoCard).getByText('1.2.0')).toBeInTheDocument();
    });

    it('shows system info card with hardware details', () => {
      renderWithRoute('pi-001');

      // Find the System Info section
      const systemCard = screen.getByRole('region', { name: /system info/i });
      expect(within(systemCard).getByText('Linux-armv7l')).toBeInTheDocument();
      expect(within(systemCard).getByText('3.11.2')).toBeInTheDocument();
      expect(within(systemCard).getByText('4096 MB')).toBeInTheDocument();
      expect(within(systemCard).getByText('4')).toBeInTheDocument();
    });

    it('shows assigned trains table with controller trains', () => {
      renderWithRoute('pi-001');

      // Both trains should be visible
      expect(screen.getByText('Test Express')).toBeInTheDocument();
      expect(screen.getByText('Freight Hauler')).toBeInTheDocument();
    });

    it('shows status as online for recent heartbeat', () => {
      renderWithRoute('pi-001');

      // Status badge should show "Online" (capitalized) with recent last_seen
      expect(screen.getByText('Online')).toBeInTheDocument();
    });

    it('back link navigates to dashboard', () => {
      renderWithRoute('pi-001');

      const backLink = screen.getByRole('link', { name: /back to dashboard/i });
      expect(backLink).toHaveAttribute('href', '/');
    });
  });

  describe('Offline Controller', () => {
    it('shows status as offline for stale heartbeat', () => {
      const offlineController = {
        ...mockController,
        last_seen: '2024-01-01T00:00:00Z', // Old = offline
      };

      vi.mocked(queries.useController).mockReturnValue({
        data: offlineController,
        isLoading: false,
        error: null,
      } as any);

      renderWithRoute('pi-001');

      expect(screen.getByText('Offline')).toBeInTheDocument();
    });
  });

  describe('No Assigned Trains', () => {
    it('shows empty state when no trains assigned', () => {
      const controllerNoTrains = {
        ...mockController,
        trains: [],
      };

      vi.mocked(queries.useController).mockReturnValue({
        data: controllerNoTrains,
        isLoading: false,
        error: null,
      } as any);

      renderWithRoute('pi-001');

      // Use getAllByText since there might be header and empty state matching
      const noTrainsElements = screen.getAllByText(/no trains assigned/i);
      expect(noTrainsElements.length).toBeGreaterThan(0);
    });
  });
});

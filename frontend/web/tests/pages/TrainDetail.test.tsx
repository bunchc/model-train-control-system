import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TrainDetail } from '@/pages/TrainDetail';
import * as queries from '@/api/queries';

// Mock the API queries - include all hooks used by TrainDetail and its children
vi.mock('@/api/queries', () => ({
  useTrains: vi.fn(),
  useTrainStatus: vi.fn(),
  useSendCommand: vi.fn(),
  useUpdateTrain: vi.fn(),
}));

/**
 * Helper to render TrainDetail with route parameters and query strings
 */
const renderWithRoute = (initialRoute: string) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={[initialRoute]}>
        <Routes>
          <Route path="/trains/:trainId" element={<TrainDetail />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>
  );
};

describe('TrainDetail', () => {
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

  // Mock train data
  const mockTrain = {
    id: 'train-001',
    name: 'Test Express',
    description: 'A test train',
    model: 'HO Scale',
    plugin: { name: 'dc_motor_hat' },
    invert_directions: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();

    Object.defineProperty(window, 'localStorage', {
      value: localStorageMock,
      writable: true,
    });
    Object.defineProperty(window, 'matchMedia', {
      value: matchMediaMock,
      writable: true,
    });

    // Default mock implementations
    vi.mocked(queries.useTrains).mockReturnValue({
      data: [mockTrain],
      isLoading: false,
      error: null,
    } as any);

    vi.mocked(queries.useTrainStatus).mockReturnValue({
      data: { train_id: 'train-001', speed: 50, direction: 'FORWARD' },
      isLoading: false,
      error: null,
    } as any);

    vi.mocked(queries.useSendCommand).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);

    vi.mocked(queries.useUpdateTrain).mockReturnValue({
      mutate: vi.fn(),
      isPending: false,
    } as any);
  });

  describe('Breadcrumb Navigation', () => {
    it('shows "Back to Dashboard" when no query params', () => {
      renderWithRoute('/trains/train-001');

      const backLink = screen.getByRole('link', { name: /back to dashboard/i });
      expect(backLink).toBeInTheDocument();
      expect(backLink).toHaveAttribute('href', '/');
    });

    it('shows "Back to {fromName}" when from and fromName present', () => {
      renderWithRoute(
        '/trains/train-001?from=/controllers/ctrl-123&fromName=Pi%20Controller'
      );

      const backLink = screen.getByRole('link', { name: /back to pi controller/i });
      expect(backLink).toBeInTheDocument();
    });

    it('back link navigates to "from" path when present', () => {
      renderWithRoute(
        '/trains/train-001?from=/controllers/ctrl-456&fromName=Test'
      );

      const backLink = screen.getByRole('link', { name: /back to test/i });
      expect(backLink).toHaveAttribute('href', '/controllers/ctrl-456');
    });

    it('handles missing fromName gracefully (shows "Back" only)', () => {
      renderWithRoute('/trains/train-001?from=/controllers/ctrl-789');

      const backLink = screen.getByRole('link', { name: /^back$/i });
      expect(backLink).toBeInTheDocument();
      expect(backLink).toHaveAttribute('href', '/controllers/ctrl-789');
    });
  });
});

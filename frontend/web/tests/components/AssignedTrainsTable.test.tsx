import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from '../utils/test-utils';
import { AssignedTrainsTable } from '@/components/controllers/AssignedTrainsTable';
import { Train } from '@/api/types';

// Helper to create mock train data
const createMockTrain = (overrides: Partial<Train> = {}): Train => ({
  id: 'train-001',
  name: 'Test Train',
  description: 'A test train',
  model: 'HO Scale',
  plugin: { name: 'dc_motor_hat' },
  invert_directions: false,
  ...overrides,
});

describe('AssignedTrainsTable', () => {
  const defaultProps = {
    trains: [createMockTrain()],
    controllerId: 'ctrl-123',
    controllerName: 'Test Controller',
  };

  describe('Table Rendering', () => {
    it('renders table headers', () => {
      render(<AssignedTrainsTable {...defaultProps} />);

      expect(screen.getByText('Name')).toBeInTheDocument();
      expect(screen.getByText('ID')).toBeInTheDocument();
      expect(screen.getByText('Plugin')).toBeInTheDocument();
      expect(screen.getByText('Model')).toBeInTheDocument();
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    it('renders train name in table row', () => {
      const trains = [createMockTrain({ name: 'Express 1' })];
      render(<AssignedTrainsTable {...defaultProps} trains={trains} />);

      expect(screen.getByText('Express 1')).toBeInTheDocument();
    });

    it('renders train ID in table row', () => {
      const trains = [createMockTrain({ id: 'train-xyz' })];
      render(<AssignedTrainsTable {...defaultProps} trains={trains} />);

      expect(screen.getByText('train-xyz')).toBeInTheDocument();
    });

    it('renders plugin name in table row', () => {
      const trains = [createMockTrain({ plugin: { name: 'stepper_motor' } })];
      render(<AssignedTrainsTable {...defaultProps} trains={trains} />);

      expect(screen.getByText('stepper_motor')).toBeInTheDocument();
    });

    it('renders model in table row', () => {
      const trains = [createMockTrain({ model: 'N Scale' })];
      render(<AssignedTrainsTable {...defaultProps} trains={trains} />);

      expect(screen.getByText('N Scale')).toBeInTheDocument();
    });

    it('displays "--" for missing model', () => {
      const trains = [createMockTrain({ model: null })];
      render(<AssignedTrainsTable {...defaultProps} trains={trains} />);

      expect(screen.getByText('--')).toBeInTheDocument();
    });

    it('renders multiple trains correctly', () => {
      const trains = [
        createMockTrain({ id: 'train-1', name: 'Train Alpha' }),
        createMockTrain({ id: 'train-2', name: 'Train Beta' }),
        createMockTrain({ id: 'train-3', name: 'Train Gamma' }),
      ];
      render(<AssignedTrainsTable {...defaultProps} trains={trains} />);

      expect(screen.getByText('Train Alpha')).toBeInTheDocument();
      expect(screen.getByText('Train Beta')).toBeInTheDocument();
      expect(screen.getByText('Train Gamma')).toBeInTheDocument();

      // Should have 3 View links
      const viewLinks = screen.getAllByRole('link', { name: /view/i });
      expect(viewLinks).toHaveLength(3);
    });
  });

  describe('Empty State', () => {
    it('renders empty state when no trains assigned', () => {
      render(<AssignedTrainsTable {...defaultProps} trains={[]} />);

      // Check for the heading specifically
      expect(
        screen.getByRole('heading', { name: /no trains assigned/i })
      ).toBeInTheDocument();
      // Table headers should NOT be visible
      expect(screen.queryByText('Actions')).not.toBeInTheDocument();
    });
  });

  describe('Navigation Links', () => {
    it('View link includes correct path', () => {
      const trains = [createMockTrain({ id: 'train-abc' })];
      render(
        <AssignedTrainsTable
          trains={trains}
          controllerId="ctrl-123"
          controllerName="Test Controller"
        />
      );

      const viewLink = screen.getByRole('link', { name: /view/i });
      expect(viewLink).toHaveAttribute('href', expect.stringContaining('/trains/train-abc'));
    });

    it('View link includes "from" query parameter', () => {
      const trains = [createMockTrain()];
      render(
        <AssignedTrainsTable
          trains={trains}
          controllerId="ctrl-456"
          controllerName="Test Controller"
        />
      );

      const viewLink = screen.getByRole('link', { name: /view/i });
      // URLSearchParams encodes / as %2F
      expect(viewLink).toHaveAttribute(
        'href',
        expect.stringContaining('from=%2Fcontrollers%2Fctrl-456')
      );
    });

    it('View link includes "fromName" query parameter', () => {
      const trains = [createMockTrain()];
      render(
        <AssignedTrainsTable
          trains={trains}
          controllerId="ctrl-123"
          controllerName="Pi Controller Alpha"
        />
      );

      const viewLink = screen.getByRole('link', { name: /view/i });
      // Spaces are encoded as +
      expect(viewLink).toHaveAttribute(
        'href',
        expect.stringContaining('fromName=Pi+Controller+Alpha')
      );
    });

    it('encodes special characters in controllerName', () => {
      const trains = [createMockTrain()];
      render(
        <AssignedTrainsTable
          trains={trains}
          controllerId="ctrl-123"
          controllerName="Controller & Special <Name>"
        />
      );

      const viewLink = screen.getByRole('link', { name: /view/i });
      const href = viewLink.getAttribute('href') ?? '';

      // Verify special characters are encoded (& becomes %26, < becomes %3C, > becomes %3E)
      expect(href).toContain('fromName=');
      expect(href).not.toContain('&Special'); // & should be encoded, not literal
      expect(href).not.toContain('<Name>'); // < and > should be encoded
    });
  });
});

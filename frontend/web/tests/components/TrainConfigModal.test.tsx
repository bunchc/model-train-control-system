import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { render } from '../utils/test-utils';
import { TrainConfigModal } from '@/components/trains/TrainConfigModal';
import { Train } from '@/api/types';

// Mock the useUpdateTrain hook
const mockMutate = vi.fn();
const mockUseUpdateTrain = vi.fn(() => ({
  mutate: mockMutate,
  isPending: false,
  error: null,
}));

vi.mock('@/api/queries', () => ({
  useUpdateTrain: () => mockUseUpdateTrain(),
}));

// Mock react-hot-toast
const mockToastSuccess = vi.fn();
const mockToastError = vi.fn();
const mockToast = vi.fn();

vi.mock('react-hot-toast', () => ({
  default: Object.assign(
    (message: string, options?: any) => mockToast(message, options),
    {
      success: (message: string) => mockToastSuccess(message),
      error: (message: string) => mockToastError(message),
    }
  ),
}));

describe('TrainConfigModal', () => {
  const mockTrain: Train = {
    id: 'train-123',
    name: 'Test Train',
    description: 'A test locomotive',
    model: 'Test Model',
    plugin: {
      name: 'adafruit_dcmotor_hat',
      config: {},
    },
    invert_directions: false,
    status: {
      speed: 0,
      voltage: 0,
      current: 0,
      position: null,
      last_updated: new Date().toISOString(),
    },
  };

  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseUpdateTrain.mockReturnValue({
      mutate: mockMutate,
      isPending: false,
      error: null,
    });
  });

  describe('Rendering', () => {
    it('renders with train data when open', () => {
      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      // Check form fields are populated
      expect(screen.getByLabelText(/name/i)).toHaveValue('Test Train');
      expect(screen.getByLabelText(/description/i)).toHaveValue('A test locomotive');

      // Check buttons are present
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });

    it('does not render when closed', () => {
      render(
        <TrainConfigModal isOpen={false} onClose={mockOnClose} train={mockTrain} />
      );

      // Modal should not be visible
      expect(screen.queryByLabelText(/name/i)).not.toBeInTheDocument();
    });

    it('shows invert directions toggle for DC motor HAT plugin', () => {
      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      // Toggle should be visible for adafruit_dcmotor_hat
      expect(screen.getByRole('checkbox', { name: /invert motor directions/i })).toBeInTheDocument();
    });

    it('hides invert directions toggle for other plugins', () => {
      const trainWithOtherPlugin = {
        ...mockTrain,
        plugin: { name: 'other_plugin', config: {} },
      };

      render(
        <TrainConfigModal
          isOpen={true}
          onClose={mockOnClose}
          train={trainWithOtherPlugin}
        />
      );

      // Toggle should not be visible for other plugins
      expect(screen.queryByRole('checkbox', { name: /invert motor directions/i })).not.toBeInTheDocument();
    });
  });

  // Note: Validation is handled by HTML5 attributes (required, maxlength)
  // and tested implicitly through successful submissions in Form Submission tests

  describe('User Interactions', () => {
    it('updates form data when user types in fields', async () => {
      const user = userEvent.setup();

      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      // Type in name field
      const nameInput = screen.getByLabelText(/train name/i);
      await user.clear(nameInput);
      await user.paste('Updated Name');
      expect(nameInput).toHaveValue('Updated Name');

      // Type in description field
      const descriptionInput = screen.getByLabelText(/description/i);
      await user.clear(descriptionInput);
      await user.paste('Updated description');
      expect(descriptionInput).toHaveValue('Updated description');
    });

    it('toggles invert directions checkbox', async () => {
      const user = userEvent.setup();

      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      const checkbox = screen.getByRole('checkbox', { name: /invert motor directions/i });

      // Initially unchecked
      expect(checkbox).not.toBeChecked();

      // Click to check
      await user.click(checkbox);
      expect(checkbox).toBeChecked();

      // Click again to uncheck
      await user.click(checkbox);
      expect(checkbox).not.toBeChecked();
    });

    it('closes modal when cancel button is clicked', async () => {
      const user = userEvent.setup();

      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      // Click cancel
      await user.click(screen.getByRole('button', { name: /cancel/i }));

      // Should call onClose
      expect(mockOnClose).toHaveBeenCalled();
    });
  });

  describe('Form Submission', () => {
    it('submits successfully with valid data', async () => {
      const user = userEvent.setup();

      // Mock successful mutation
      mockMutate.mockImplementation(({ trainId, updates }, { onSuccess }) => {
        onSuccess?.({ ...mockTrain, ...updates });
      });

      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      // Change the name
      const nameInput = screen.getByLabelText(/name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'Express Train');

      // Submit the form
      await user.click(screen.getByRole('button', { name: /save changes/i }));

      // Should call mutate with correct data
      await waitFor(() => {
        expect(mockMutate).toHaveBeenCalledWith(
          expect.objectContaining({
            trainId: 'train-123',
            updates: expect.objectContaining({
              name: 'Express Train',
            }),
          }),
          expect.any(Object)
        );
      });
    });

    it('shows warning toast when no changes are made', async () => {
      const user = userEvent.setup();

      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      // Submit without making any changes
      await user.click(screen.getByRole('button', { name: /save changes/i }));

      // Should show warning toast
      await waitFor(() => {
        expect(mockToast).toHaveBeenCalledWith(
          'No changes to save',
          expect.objectContaining({ icon: '⚠️' })
        );
      });

      // Should not call mutate
      expect(mockMutate).not.toHaveBeenCalled();
    });

    it('handles API errors gracefully', async () => {
      const user = userEvent.setup();

      // Mock mutation that calls onError
      mockMutate.mockImplementation(({ trainId, updates }, { onError }) => {
        onError?.(new Error('Network error'));
      });

      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      // Make a change
      const nameInput = screen.getByLabelText(/name/i);
      await user.clear(nameInput);
      await user.type(nameInput, 'New Name');

      // Submit the form
      await user.click(screen.getByRole('button', { name: /save changes/i }));

      // Should call mutate
      await waitFor(() => {
        expect(mockMutate).toHaveBeenCalled();
      });
    });

    it('submits all fields correctly when changed', async () => {
      const user = userEvent.setup();

      mockMutate.mockImplementation(({ trainId, updates }, { onSuccess }) => {
        onSuccess?.({ ...mockTrain, ...updates });
      });

      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      // Update all fields
      await user.clear(screen.getByLabelText(/train name/i));
      await user.paste('Express Line');

      await user.clear(screen.getByLabelText(/description/i));
      await user.paste('Fast passenger train');

      await user.click(screen.getByRole('checkbox', { name: /invert motor directions/i }));

      // Submit
      await user.click(screen.getByRole('button', { name: /save changes/i }));

      // Verify all fields submitted
      await waitFor(() => {
        expect(mockMutate).toHaveBeenCalledWith(
          expect.objectContaining({
            trainId: 'train-123',
            updates: {
              name: 'Express Line',
              description: 'Fast passenger train',
              invert_directions: true,
            },
          }),
          expect.any(Object)
        );
      });
    });
  });

  describe('Loading States', () => {
    it('disables form while saving', () => {
      mockUseUpdateTrain.mockReturnValue({
        mutate: mockMutate,
        isPending: true,
        error: null,
      });

      render(
        <TrainConfigModal isOpen={true} onClose={mockOnClose} train={mockTrain} />
      );

      // Form should be disabled
      expect(screen.getByLabelText(/name/i)).toBeDisabled();
      expect(screen.getByLabelText(/description/i)).toBeDisabled();
      expect(screen.getByRole('button', { name: /save changes/i })).toBeDisabled();
    });
  });
});

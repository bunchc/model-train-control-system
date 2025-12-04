import React, { useState, useEffect, useRef } from 'react';
import toast from 'react-hot-toast';
import { Modal } from '@/components/ui/Modal';
import { Input } from '@/components/ui/Input';
import { Textarea } from '@/components/ui/Textarea';
import { Button } from '@/components/ui/Button';
import { useUpdateTrain } from '@/api/queries';
import { Train } from '@/api/types';

interface TrainConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  train: Train;
}

interface FormErrors {
  name?: string;
  description?: string;
}

/**
 * Modal for editing train configuration (name, description, direction inversion)
 */
export const TrainConfigModal: React.FC<TrainConfigModalProps> = ({ isOpen, onClose, train }) => {
  const [formData, setFormData] = useState({
    name: train.name,
    description: train.description || '',
    invert_directions: train.invert_directions || false,
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const { mutate, isPending, error: mutationError } = useUpdateTrain();
  const nameInputRef = useRef<HTMLInputElement>(null);

  // Reset form when train changes or modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        name: train.name,
        description: train.description || '',
        invert_directions: train.invert_directions || false,
      });
      setErrors({});

      // Task 8.4: Auto-focus first input for better UX
      setTimeout(() => nameInputRef.current?.focus(), 100);
    }
  }, [isOpen, train]);

  /**
   * Validate form fields
   * Returns true if valid, false if errors exist
   */
  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};
    const trimmedName = formData.name.trim();

    // Name is required
    if (!trimmedName) {
      newErrors.name = 'Train name is required';
    } else if (trimmedName.length > 100) {
      newErrors.name = 'Name must be 100 characters or less';
    }

    // Description is optional but has max length
    if (formData.description && formData.description.length > 500) {
      newErrors.description = 'Description must be 500 characters or less';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submission
   */
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) return;

    // Check if anything actually changed (Task 8.1: No changes warning)
    const hasChanges =
      formData.name.trim() !== train.name ||
      (formData.description.trim() || null) !== train.description ||
      formData.invert_directions !== (train.invert_directions || false);

    if (!hasChanges) {
      toast('No changes to save', { icon: '⚠️' });
      return;
    }

    mutate(
      {
        trainId: train.id,
        updates: {
          name: formData.name.trim(),
          description: formData.description.trim() || null,
          invert_directions: formData.invert_directions,
        },
      },
      {
        onSuccess: () => {
          // Task 8.1: Success toast
          toast.success('Train configuration updated');
          onClose();
        },
        onError: (error: any) => {
          // Task 8.1: Error toast
          const errorMessage = error?.response?.data?.detail || 'Failed to update train configuration';
          toast.error(errorMessage);
        },
      }
    );
  };

  /**
   * Handle cancel - reset form and close
   */
  const handleCancel = () => {
    setFormData({
      name: train.name,
      description: train.description || '',
      invert_directions: train.invert_directions || false,
    });
    setErrors({});
    onClose();
  };

  /**
   * Clear field error when user starts typing
   */
  const handleFieldChange = (field: keyof typeof formData, value: string | boolean) => {
    setFormData({ ...formData, [field]: value });

    // Clear error for this field
    if (field in errors) {
      setErrors({ ...errors, [field]: undefined });
    }
  };

  // Check if plugin supports direction inversion (only DC motor HAT for now)
  const showInvertToggle = train.plugin?.name === 'adafruit_dcmotor_hat';

  return (
    <Modal
      isOpen={isOpen}
      onClose={isPending ? () => {} : handleCancel}  // Task 8.3: Prevent close during save
      title="Train Configuration"
      size="md"
    >
      <form onSubmit={handleSubmit} className="space-y-4" aria-busy={isPending}>
        {/* Name field - Required */}
        <Input
          ref={nameInputRef}
          label="Train Name"
          value={formData.name}
          onChange={(e) => handleFieldChange('name', e.target.value)}
          error={errors.name}
          disabled={isPending}
          required
          maxLength={100}
          placeholder="e.g., Express Line Engine"
        />

        {/* Description field - Optional */}
        <Textarea
          label="Description (optional)"
          value={formData.description}
          onChange={(e) => handleFieldChange('description', e.target.value)}
          error={errors.description}
          disabled={isPending}
          rows={3}
          maxLength={500}
          placeholder="Add notes about this train..."
        />

        {/* Invert directions toggle - Conditional on plugin type */}
        {showInvertToggle && (
          <div className="flex items-start space-x-2 rounded-md border border-gray-200 p-3 dark:border-gray-700">
            <input
              type="checkbox"
              id="invert_directions"
              checked={formData.invert_directions}
              onChange={(e) => handleFieldChange('invert_directions', e.target.checked)}
              disabled={isPending}
              className="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            />
            <div className="flex-1">
              <label
                htmlFor="invert_directions"
                className="block text-sm font-medium text-gray-700 dark:text-gray-300"
              >
                Invert motor directions
              </label>
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Swap forward/backward commands (useful if motor is mounted backwards)
              </p>
            </div>
          </div>
        )}

        {/* API Error display */}
        {mutationError && (
          <div className="rounded-md bg-red-50 p-3 dark:bg-red-900/20">
            <p className="text-sm text-red-800 dark:text-red-200">
              {(mutationError as any)?.response?.data?.detail || 'Failed to update train configuration'}
            </p>
          </div>
        )}

        {/* Character count helpers */}
        <div className="text-xs text-gray-500 dark:text-gray-400">
          <div>Name: {formData.name.length}/100 characters</div>
          {formData.description && <div>Description: {formData.description.length}/500 characters</div>}
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-3 border-t border-gray-200 pt-4 dark:border-gray-700">
          <Button type="button" variant="secondary" onClick={handleCancel} disabled={isPending}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" isLoading={isPending}>
            Save Changes
          </Button>
        </div>
      </form>
    </Modal>
  );
};

import React from 'react';
import { cn } from '@/utils/cn';
import { Spinner } from './Spinner';

export interface LoadingStateProps {
  message?: string;
  className?: string;
}

/**
 * Loading state component with spinner
 */
export const LoadingState: React.FC<LoadingStateProps> = ({ message = 'Loading...', className }) => {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12', className)} role="status" aria-live="polite">
      <Spinner className="h-12 w-12" />
      <p className="mt-4 text-sm text-gray-600 dark:text-gray-400">{message}</p>
    </div>
  );
};

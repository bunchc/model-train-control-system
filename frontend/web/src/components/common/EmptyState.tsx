import React from 'react';
import { cn } from '@/utils/cn';

export interface EmptyStateProps {
  title: string;
  description?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
  className?: string;
}

/**
 * Empty state component for lists with no data
 */
export const EmptyState: React.FC<EmptyStateProps> = ({ title, description, action, icon, className }) => {
  return (
    <div className={cn('flex flex-col items-center justify-center py-12 text-center', className)}>
      {icon && <div className="mb-4 text-gray-400 dark:text-gray-600">{icon}</div>}
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
      {description && <p className="mt-2 max-w-md text-sm text-gray-600 dark:text-gray-400">{description}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  );
};

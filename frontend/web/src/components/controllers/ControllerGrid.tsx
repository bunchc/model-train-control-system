import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ControllerCard } from './ControllerCard';
import { EdgeController } from '@/api/types';
import { EmptyState } from '@/components/common/EmptyState';
import { ServerIcon } from '@heroicons/react/24/outline';

export interface ControllerGridProps {
  controllers: EdgeController[];
}

/**
 * Responsive grid of controller cards
 */
export const ControllerGrid: React.FC<ControllerGridProps> = ({ controllers }) => {
  const navigate = useNavigate();

  // Debug: Log controllers prop for diagnosis
  if (process.env.NODE_ENV !== 'production') {
    // eslint-disable-next-line no-console
    console.debug('ControllerGrid controllers:', controllers);
  }

  // Filter out controllers with missing or invalid IDs
  const validControllers = controllers.filter(c => typeof c.id === 'string' && c.id.length > 0);

  if (validControllers.length === 0) {
    return (
      <EmptyState
        title="No controllers configured"
        description="Edge controllers will appear here once they're registered and send their first heartbeat."
        icon={<ServerIcon className="h-16 w-16" />}
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3" data-testid="controller-grid">
      {validControllers.map((controller) => (
        <ControllerCard
          key={controller.id}
          controller={controller}
          onClick={() => navigate(`/controllers/${controller.id}`)}
        />
      ))}
    </div>
  );
};

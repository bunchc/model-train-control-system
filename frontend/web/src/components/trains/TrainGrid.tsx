import React from 'react';
import { TrainCard } from './TrainCard';
import { Train } from '@/api/types';
import { EmptyState } from '@/components/common/EmptyState';
import { RocketLaunchIcon } from '@heroicons/react/24/outline';

export interface TrainGridProps {
  trains: Train[];
}

/**
 * Responsive grid of train cards
 */
export const TrainGrid: React.FC<TrainGridProps> = ({ trains }) => {
  if (trains.length === 0) {
    return (
      <EmptyState
        title="No trains configured"
        description="Add a train configuration to get started with controlling your model trains."
        icon={<RocketLaunchIcon className="h-16 w-16" />}
      />
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {trains.map((train) => (
        <TrainCard key={train.id} train={train} />
      ))}
    </div>
  );
};

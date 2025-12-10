import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { ControllerGrid } from './ControllerGrid';
import { EdgeController } from '@/api/types';

describe('ControllerGrid', () => {
  const mockControllers: EdgeController[] = [
    {
      id: 'test-uuid-1',
      name: 'Test Controller 1',
      description: 'First test controller',
      address: '192.168.1.100',
      enabled: true,
      trains: [],
      first_seen: '2025-12-09T12:00:00Z',
      last_seen: '2025-12-09T12:05:00Z',
      config_hash: null,
      version: '1.0.0',
      platform: 'Linux',
      python_version: '3.9.25',
      memory_mb: 1024,
      cpu_count: 4,
      status: 'online',
    },
  ];

  it('renders controller cards for valid controllers', () => {
    render(
      <MemoryRouter>
        <ControllerGrid controllers={mockControllers} />
      </MemoryRouter>
    );
    expect(screen.getByTestId('controller-card-test-uuid-1')).toBeInTheDocument();
    expect(screen.queryByText('No controllers configured')).not.toBeInTheDocument();
  });

  it('shows empty state when no controllers', () => {
    render(
      <MemoryRouter>
        <ControllerGrid controllers={[]} />
      </MemoryRouter>
    );
    expect(screen.getByText('No controllers configured')).toBeInTheDocument();
  });

  it('filters out controllers with invalid IDs', () => {
    const invalidControllers = [
      { ...mockControllers[0], id: '' },
      { ...mockControllers[0], id: null },
    ];
    render(
      <MemoryRouter>
        <ControllerGrid controllers={invalidControllers as any} />
      </MemoryRouter>
    );
    expect(screen.getByText('No controllers configured')).toBeInTheDocument();
  });
});

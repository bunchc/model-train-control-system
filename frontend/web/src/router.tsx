import React from 'react';
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { Dashboard } from '@/pages/Dashboard';
import { TrainDetail } from '@/pages/TrainDetail';
import { Configuration } from '@/pages/Configuration';
import { Controllers } from '@/pages/Controllers';
import { NotFound } from '@/pages/NotFound';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';

/**
 * Application router configuration
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <Dashboard />,
    errorElement: <ErrorBoundary />,
  },
  {
    path: '/trains/:trainId',
    element: <TrainDetail />,
    errorElement: <ErrorBoundary />,
  },
  {
    path: '/config',
    element: <Configuration />,
    errorElement: <ErrorBoundary />,
  },
  {
    path: '/controllers',
    element: <Controllers />,
    errorElement: <ErrorBoundary />,
  },
  {
    path: '*',
    element: <NotFound />,
  },
]);

/**
 * Router provider component
 */
export const AppRouter: React.FC = () => {
  return <RouterProvider router={router} />;
};

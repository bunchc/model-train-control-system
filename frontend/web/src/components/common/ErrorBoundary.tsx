import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { PageLayout } from '@/components/layout/PageLayout';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

interface Props {
  children?: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

/**
 * Error boundary component to catch React errors
 */
export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Uncaught error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <PageLayout>
          <div className="flex min-h-[60vh] flex-col items-center justify-center">
            <div className="max-w-md rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-900/20">
              <div className="flex items-center gap-3">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-600 dark:text-red-400" aria-hidden="true" />
                <div>
                  <h2 className="text-xl font-semibold text-red-900 dark:text-red-200">Something went wrong</h2>
                  <p className="mt-2 text-sm text-red-700 dark:text-red-300">
                    {this.state.error?.message || 'An unexpected error occurred'}
                  </p>
                </div>
              </div>
              <div className="mt-4 flex gap-3">
                <button
                  onClick={() => window.location.reload()}
                  className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                >
                  Reload Page
                </button>
                <Link
                  to="/"
                  className="rounded-md border border-red-300 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 dark:border-red-700 dark:text-red-300 dark:hover:bg-red-900/30"
                >
                  Go to Dashboard
                </Link>
              </div>
            </div>
          </div>
        </PageLayout>
      );
    }

    return this.props.children;
  }
}

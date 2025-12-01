import { QueryClient } from '@tanstack/react-query';

/**
 * React Query client configuration
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5000,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});

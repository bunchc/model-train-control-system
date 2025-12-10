import { useQuery, useMutation, useQueryClient, UseQueryResult, UseMutationResult } from '@tanstack/react-query';
import { Train, TrainStatus, TrainCommand, TrainUpdateRequest, EdgeController, Plugin, FullConfig } from './types';
import { getTrains, sendTrainCommand, getTrainStatus, updateTrain } from './endpoints/trains';
import { getFullConfig, getConfigTrains, getPlugins } from './endpoints/config';
import { getControllers, getControllerConfig } from './endpoints/controllers';

/**
 * Query keys for cache management
 */
export const queryKeys = {
  trains: ['trains'] as const,
  trainStatus: (id: string) => ['trains', id, 'status'] as const,
  controllers: ['controllers'] as const,
  controller: (id: string) => ['controllers', id] as const,
  plugins: ['plugins'] as const,
  config: ['config'] as const,
  configTrains: ['config', 'trains'] as const,
};

/**
 * Hook: Fetch all trains
 * Auto-refresh every 5 seconds
 */
export const useTrains = (): UseQueryResult<Train[], Error> => {
  return useQuery({
    queryKey: queryKeys.trains,
    queryFn: getTrains,
    refetchInterval: 5000, // Refresh every 5 seconds
    staleTime: 3000,
  });
};

/**
 * Hook: Fetch train status
 * Auto-refresh every 2 seconds for real-time telemetry
 * Only polls after initial successful fetch to avoid hammering on 404s
 */
export const useTrainStatus = (trainId: string): UseQueryResult<TrainStatus, Error> => {
  return useQuery({
    queryKey: queryKeys.trainStatus(trainId),
    queryFn: () => getTrainStatus(trainId),
    refetchInterval: (data) => {
      // Only poll if we've successfully fetched data at least once
      // This prevents continuous polling when status doesn't exist (404)
      return data ? 2000 : false;
    },
    retry: (failureCount, error: any) => {
      // Don't retry on 404 (status not found)
      if (error?.response?.status === 404) {
        return false;
      }
      // Retry other errors up to 3 times
      return failureCount < 3;
    },
    enabled: !!trainId,
  });
};

/**
 * Hook: Send command to train
 * Invalidates train status cache on success
 */
export const useSendCommand = (): UseMutationResult<
  { message: string },
  Error,
  { trainId: string; command: TrainCommand }
> => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ trainId, command }) => sendTrainCommand(trainId, command),
    onSuccess: (_, variables) => {
      // Invalidate train status to force refresh
      queryClient.invalidateQueries({ queryKey: queryKeys.trainStatus(variables.trainId) });
    },
  });
};

/**
 * Hook: Update train configuration
 * Invalidates trains cache on success to trigger re-fetch
 */
export const useUpdateTrain = (): UseMutationResult<
  Train,
  Error,
  { trainId: string; updates: TrainUpdateRequest }
> => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ trainId, updates }) => updateTrain(trainId, updates),
    onSuccess: () => {
      // Invalidate trains list to force refresh
      queryClient.invalidateQueries({ queryKey: queryKeys.trains });
      // Also invalidate config trains if they're separate
      queryClient.invalidateQueries({ queryKey: queryKeys.configTrains });
    },
  });
};

/**
 * Hook: Fetch all edge controllers
 * Polls every 10 seconds to keep status indicators current
 */
export const useControllers = (): UseQueryResult<EdgeController[], Error> => {
  return useQuery({
    queryKey: queryKeys.controllers,
    queryFn: getControllers,
    refetchInterval: 10000, // Poll every 10 seconds for status updates
    staleTime: 5000,        // Consider stale after 5 seconds
  });
};

/**
 * Hook: Fetch controller by ID
 */
export const useController = (controllerId: string): UseQueryResult<EdgeController, Error> => {
  return useQuery({
    queryKey: queryKeys.controller(controllerId),
    queryFn: () => getControllerConfig(controllerId),
    enabled: !!controllerId,
  });
};

/**
 * Hook: Fetch all plugins
 */
export const usePlugins = (): UseQueryResult<Plugin[], Error> => {
  return useQuery({
    queryKey: queryKeys.plugins,
    queryFn: getPlugins,
    staleTime: 30000, // Plugins rarely change
  });
};

/**
 * Hook: Fetch full system configuration
 */
export const useFullConfig = (): UseQueryResult<FullConfig, Error> => {
  return useQuery({
    queryKey: queryKeys.config,
    queryFn: getFullConfig,
    staleTime: 10000,
  });
};

/**
 * Hook: Fetch configured trains
 */
export const useConfigTrains = (): UseQueryResult<Train[], Error> => {
  return useQuery({
    queryKey: queryKeys.configTrains,
    queryFn: getConfigTrains,
    staleTime: 10000,
  });
};

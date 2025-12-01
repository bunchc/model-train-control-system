import { apiClient } from '../client';
import { FullConfig, Train, Plugin, EdgeController } from '../types';

/**
 * Get full system configuration
 */
export const getFullConfig = async (): Promise<FullConfig> => {
  const response = await apiClient.get<FullConfig>('/api/config');
  return response.data;
};

/**
 * List all configured trains
 */
export const getConfigTrains = async (): Promise<Train[]> => {
  const response = await apiClient.get<Train[]>('/api/config/trains');
  return response.data;
};

/**
 * Get train configuration by ID
 */
export const getTrainConfig = async (trainId: string): Promise<Train> => {
  const response = await apiClient.get<Train>(`/api/config/trains/${trainId}`);
  return response.data;
};

/**
 * List available plugins
 */
export const getPlugins = async (): Promise<Plugin[]> => {
  const response = await apiClient.get<Plugin[]>('/api/plugins');
  return response.data;
};

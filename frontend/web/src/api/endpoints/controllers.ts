import { apiClient } from '../client';
import { ControllerHeartbeat, EdgeController } from '../types';

/**
 * List all edge controllers
 */
export const getControllers = async (): Promise<EdgeController[]> => {
  const response = await apiClient.get<EdgeController[]>('/api/controllers');
  return response.data;
};

/**
 * Get edge controller configuration by ID
 */
export const getControllerConfig = async (controllerId: string): Promise<EdgeController> => {
  const response = await apiClient.get<EdgeController>(
    `/api/config/edge-controllers/${controllerId}`
  );
  return response.data;
};

/**
 * Send heartbeat for an edge controller
 * Used primarily for testing - real heartbeats come from edge controllers
 */
export const sendHeartbeat = async (
  controllerId: string,
  heartbeat: ControllerHeartbeat
): Promise<{ status: string }> => {
  const response = await apiClient.post<{ status: string }>(
    `/api/controllers/${controllerId}/heartbeat`,
    heartbeat
  );
  return response.data;
};

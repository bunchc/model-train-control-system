import { apiClient } from '../client';
import { Train, TrainStatus, TrainCommand, TrainUpdateRequest } from '../types';

/**
 * Fetch all trains
 */
export const getTrains = async (): Promise<Train[]> => {
  const response = await apiClient.get<Train[]>('/api/trains');
  return response.data;
};

/**
 * Send command to specific train
 */
export const sendTrainCommand = async (
  trainId: string,
  command: TrainCommand
): Promise<{ message: string }> => {
  const response = await apiClient.post<{ message: string }>(
    `/api/trains/${trainId}/command`,
    command
  );
  return response.data;
};

/**
 * Get train status from database
 */
export const getTrainStatus = async (trainId: string): Promise<TrainStatus> => {
  const response = await apiClient.get<TrainStatus>(`/api/trains/${trainId}/status`);
  return response.data;
};

/**
 * Update train configuration (partial update)
 */
export const updateTrain = async (
  trainId: string,
  updates: TrainUpdateRequest
): Promise<Train> => {
  const response = await apiClient.put<Train>(
    `/api/trains/${trainId}`,
    updates
  );
  return response.data;
};

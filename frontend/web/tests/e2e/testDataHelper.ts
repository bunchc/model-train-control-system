// testDataHelper.ts
// Helper to fetch controller and train IDs from the backend for Playwright E2E tests

import { APIRequestContext } from '@playwright/test';

export async function getControllerIds(request: APIRequestContext): Promise<string[]> {
  const response = await request.get('/api/controllers');
  if (!response.ok()) throw new Error('Failed to fetch controllers');
  const controllers = await response.json();
  if (!Array.isArray(controllers) || !controllers.length) {
    throw new Error('No controllers found. Please seed test data before running E2E tests.');
  }
  return controllers.map((c: any) => c.id);
}

export async function getTrainIds(request: APIRequestContext): Promise<string[]> {
  const response = await request.get('/api/trains');
  if (!response.ok()) throw new Error('Failed to fetch trains');
  const trains = await response.json();
  if (!Array.isArray(trains) || !trains.length) {
    throw new Error('No trains found. Please seed test data before running E2E tests.');
  }
  return trains.map((t: any) => t.id);
}

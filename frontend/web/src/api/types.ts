/**
 * TypeScript types generated from OpenAPI specification
 * Model Train Control System API v0.1.0
 */

export interface PluginConfig {
  i2c_address?: string | null;
  port?: number | null;
  default_speed?: number | null;
  enabled?: boolean | null;
  [key: string]: unknown;
}

export interface Plugin {
  name: string;
  description?: string | null;
  config?: Record<string, unknown>;
}

export interface TrainPlugin {
  name: string;
  config?: Record<string, unknown>;
}

export interface Train {
  id: string;
  name: string;
  description?: string | null;
  model?: string | null;
  plugin: TrainPlugin;
}

export interface TrainStatus {
  train_id: string;
  speed: number;
  direction: 'FORWARD' | 'BACKWARD';
  timestamp?: string;
}

export interface TrainCommand {
  action: 'setSpeed' | 'start' | 'stop' | 'forward' | 'reverse' | 'emergencyStop';
  speed?: number | null;
  direction?: 'forward' | 'reverse' | null;
}

export interface EdgeController {
  id: string;
  name: string;
  description?: string | null;
  address?: string | null;
  enabled?: boolean;
  trains?: Train[];
}

export interface FullConfig {
  plugins?: Plugin[];
  edge_controllers?: EdgeController[];
}

export interface HTTPValidationError {
  detail?: ValidationError[];
}

export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

// API Response wrappers
export interface ApiResponse<T> {
  data: T;
  status: number;
}

export interface ApiError {
  detail: string | ValidationError[];
}

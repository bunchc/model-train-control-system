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
  invert_directions?: boolean;
}

export interface TrainUpdateRequest {
  name?: string;
  description?: string | null;
  invert_directions?: boolean;
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

/**
 * Controller status derived from last_seen timestamp
 */
export type ControllerStatus = 'online' | 'offline' | 'unknown';

export interface EdgeController {
  id: string;
  name: string;
  description?: string | null;
  address?: string | null;
  enabled?: boolean;
  trains?: Train[];

  // Telemetry fields (populated by heartbeat)
  first_seen?: string | null;
  last_seen?: string | null;
  config_hash?: string | null;
  version?: string | null;
  platform?: string | null;
  python_version?: string | null;
  memory_mb?: number | null;
  cpu_count?: number | null;
  status?: ControllerStatus | null;
}

/**
 * Heartbeat payload sent by edge controllers
 */
export interface ControllerHeartbeat {
  config_hash?: string;
  version?: string;
  platform?: string;
  python_version?: string;
  memory_mb?: number;
  cpu_count?: number;
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

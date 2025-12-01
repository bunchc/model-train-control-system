/**
 * Application constants
 */

export const APP_NAME = 'Model Train Control System';
export const APP_VERSION = '1.0.0';

/**
 * API polling intervals (milliseconds)
 */
export const POLLING_INTERVALS = {
  TRAIN_STATUS: 2000, // 2 seconds
  TRAIN_LIST: 5000, // 5 seconds
  CONTROLLERS: 10000, // 10 seconds
  PLUGINS: 30000, // 30 seconds
} as const;

/**
 * Train command actions
 */
export const TRAIN_ACTIONS = {
  SET_SPEED: 'setSpeed',
  START: 'start',
  STOP: 'stop',
  FORWARD: 'forward',
  REVERSE: 'reverse',
} as const;

/**
 * Speed limits
 */
export const SPEED_LIMITS = {
  MIN: 0,
  MAX: 100,
  DEFAULT: 50,
} as const;

/**
 * Theme modes
 */
export const THEMES = {
  LIGHT: 'light',
  DARK: 'dark',
  SYSTEM: 'system',
} as const;

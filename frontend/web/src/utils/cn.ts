import { clsx, type ClassValue } from 'clsx';

/**
 * Merge Tailwind CSS classes with conflict resolution
 * Usage: cn('p-4', isDark && 'bg-gray-800', 'hover:bg-blue-500')
 */
export function cn(...inputs: ClassValue[]): string {
  return clsx(inputs);
}

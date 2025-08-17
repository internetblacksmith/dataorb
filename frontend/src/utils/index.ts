// Utility functions

import { DataOrbStats } from '../types';

/**
 * Format large numbers with K/M suffixes
 */
export const formatNumber = (num: number): string => {
  if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
  if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
  return num.toString();
};

/**
 * Format time to HH:MM:SS
 */
export const formatTime = (date: Date): string => {
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false,
  });
};

/**
 * Format date to readable string
 */
export const formatDate = (date: Date): string => {
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
};

/**
 * Get trend icon based on value
 */
export const getTrendIcon = (trend?: number): string => {
  if (!trend) return '';
  return trend > 0 ? '+' : '-';
};

/**
 * Get trend class for styling
 */
export const getTrendClass = (trend?: number): string => {
  if (!trend) return 'neutral';
  return trend > 0 ? 'up' : 'down';
};

/**
 * Calculate mock trend (temporary until backend provides it)
 */
export const calculateMockTrend = (): number => {
  return Math.random() > 0.5 ? Math.random() * 20 : -Math.random() * 20;
};

/**
 * Get metric value from stats object
 */
export const getMetricValue = (
  stats: DataOrbStats | null,
  metricType: string
): number => {
  if (!stats) return 0;
  
  // The metricType is already the stats key (e.g., "events_24h")
  const statsKey = metricType as keyof DataOrbStats;
  
  const value = stats[statsKey];
  return typeof value === 'number' ? value : 0;
};

/**
 * Get default label for a metric type
 */
export const getDefaultMetricLabel = (metricType: string): string => {
  const labels: Record<string, string> = {
    'events_24h': 'Events (24h)',
    'unique_users_24h': 'Users (24h)',
    'page_views_24h': 'Page Views (24h)',
    'custom_events_24h': 'Custom Events',
    'sessions_24h': 'Sessions (24h)',
    'events_1h': 'Events (1h)',
    'avg_events_per_user': 'Avg/User',
    'new_users_24h': 'New Users',
    'returning_users_24h': 'Returning Users',
    'bounce_rate': 'Bounce Rate',
    'avg_session_duration': 'Avg Duration',
  };
  
  return labels[metricType] || metricType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
};

/**
 * Format percentage
 */
export const formatPercentage = (value: number, decimals: number = 1): string => {
  return `${value.toFixed(decimals)}%`;
};

/**
 * Calculate percentage change
 */
export const calculatePercentageChange = (current: number, previous: number): number => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
};

/**
 * Debounce function
 */
export const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
};

/**
 * Throttle function
 */
export const throttle = <T extends (...args: any[]) => any>(
  func: T,
  limit: number
): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean;
  
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => (inThrottle = false), limit);
    }
  };
};

/**
 * Check if running on local display
 */
export const isLocalDisplay = (): boolean => {
  return (
    window.location.hostname === 'localhost' ||
    window.location.hostname === '127.0.0.1'
  );
};

/**
 * Check if running on AP network
 */
export const isAPNetwork = (): boolean => {
  return (
    window.location.hostname === '192.168.4.1' ||
    window.location.hostname.startsWith('192.168.4.')
  );
};

/**
 * Parse error message from response
 */
export const parseErrorMessage = (error: any): string => {
  if (typeof error === 'string') return error;
  if (error?.message) return error.message;
  if (error?.error) return error.error;
  return 'An unexpected error occurred';
};

/**
 * Generate random ID
 */
export const generateId = (): string => {
  return Math.random().toString(36).substring(2) + Date.now().toString(36);
};

/**
 * Deep clone object
 */
export const deepClone = <T>(obj: T): T => {
  return JSON.parse(JSON.stringify(obj));
};

/**
 * Merge objects deeply
 */
export const deepMerge = <T extends Record<string, any>>(
  target: T,
  ...sources: Partial<T>[]
): T => {
  if (!sources.length) return target;
  const source = sources.shift();

  if (source) {
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        if (!target[key]) Object.assign(target, { [key]: {} });
        deepMerge(target[key] as any, source[key] as any);
      } else {
        Object.assign(target, { [key]: source[key] });
      }
    }
  }

  return deepMerge(target, ...sources);
};
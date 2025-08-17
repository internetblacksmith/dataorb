import { useState, useEffect, useCallback, useRef } from 'react';
import { AnalyticsDashboardStats } from '../types';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../constants';

/**
 * Custom hook specifically for Analytics dashboard stats
 */
export const useAnalyticsDashboard = (refreshInterval: number = REFRESH_INTERVALS.STATS) => {
  const [stats, setStats] = useState<AnalyticsDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout>();
  
  // Enforce minimum 30-second interval to avoid excessive API calls
  const safeInterval = Math.max(refreshInterval, REFRESH_INTERVALS.STATS);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.STATS_ANALYTICS);
      const data = await response.json();

      if (data.error) {
        setError(data.error);
        setStats(null);
      } else {
        setStats(data as AnalyticsDashboardStats);
        setError(null);
      }
    } catch (err) {
      setError('Failed to fetch Analytics dashboard stats');
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial fetch
  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  // Set up refresh interval with enforced minimum
  useEffect(() => {
    if (safeInterval > 0) {
      intervalRef.current = setInterval(fetchStats, safeInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [fetchStats, safeInterval]);

  return {
    stats,
    loading,
    error,
    refetch: fetchStats,
    // Convenience getters for metrics
    centerMetric: stats?.center || null,
    topMetric: stats?.top || null,
    leftMetric: stats?.left || null,
    rightMetric: stats?.right || null,
    bottomMetric: stats?.bottom || null,
    stat1: stats?.stat1 || null,
    stat2: stats?.stat2 || null,
    stat3: stats?.stat3 || null,
    demoMode: stats?.demo_mode || false,
    deviceIp: stats?.device_ip || 'Unknown',
    lastUpdated: stats?.lastUpdated || null,
  };
};
import { useState, useEffect, useCallback, useRef } from 'react';
import { ExecutiveDashboardStats } from '../types';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../constants';

/**
 * Custom hook specifically for Executive dashboard stats
 */
export const useExecutiveDashboard = (refreshInterval: number = REFRESH_INTERVALS.STATS) => {
  const [stats, setStats] = useState<ExecutiveDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout>();
  
  // Enforce minimum 30-second interval to avoid excessive API calls
  const safeInterval = Math.max(refreshInterval, REFRESH_INTERVALS.STATS);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.STATS_EXECUTIVE);
      const data = await response.json();

      if (data.error) {
        setError(data.error);
        setStats(null);
      } else {
        setStats(data as ExecutiveDashboardStats);
        setError(null);
      }
    } catch (err) {
      setError('Failed to fetch Executive dashboard stats');
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
    // Convenience getters for cardinal directions
    northMetric: stats?.north || null,
    eastMetric: stats?.east || null,
    southMetric: stats?.south || null,
    westMetric: stats?.west || null,
    // Convenience getters for diagonal positions
    northEastMetric: stats?.northEast || null,
    southEastMetric: stats?.southEast || null,
    southWestMetric: stats?.southWest || null,
    northWestMetric: stats?.northWest || null,
    demoMode: stats?.demo_mode || false,
    deviceIp: stats?.device_ip || 'Unknown',
    lastUpdated: stats?.lastUpdated || null,
  };
};
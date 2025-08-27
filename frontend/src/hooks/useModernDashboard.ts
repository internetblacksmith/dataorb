import { useState, useEffect, useCallback, useRef } from 'react';
import { ModernDashboardStats } from '../types';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../constants';
import { handleNetworkError } from '../utils/networkErrorHandler';

/**
 * Custom hook specifically for Modern dashboard stats
 */
export const useModernDashboard = (refreshInterval: number = REFRESH_INTERVALS.STATS) => {
  const [stats, setStats] = useState<ModernDashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout>();
  
  // Enforce minimum 30-second interval to avoid excessive API calls
  const safeInterval = Math.max(refreshInterval, REFRESH_INTERVALS.STATS);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.STATS_MODERN);
      const data = await response.json();

      if (data.error) {
        // Check for network error first
        if (!handleNetworkError(data, setError, setStats)) {
          setError(data.error);
          setStats(null);
        }
      } else {
        setStats(data as ModernDashboardStats);
        setError(null);
      }
    } catch (err) {
      setError('Failed to fetch Modern dashboard stats');
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
    primaryMetric: stats?.primary || null,
    secondaryLeftMetric: stats?.secondaryLeft || null,
    secondaryRightMetric: stats?.secondaryRight || null,
    miniStat1: stats?.miniStat1 || null,
    miniStat2: stats?.miniStat2 || null,
    miniStat3: stats?.miniStat3 || null,
    demoMode: stats?.demo_mode || false,
    deviceIp: stats?.device_ip || 'Unknown',
    lastUpdated: stats?.lastUpdated || null,
  };
};
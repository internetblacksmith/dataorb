import { useState, useEffect, useCallback, useRef } from 'react';
import { 
  ClassicDashboardStats, 
  ModernDashboardStats, 
  AnalyticsDashboardStats, 
  ExecutiveDashboardStats 
} from '../types';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../constants';

type DashboardStats = ClassicDashboardStats | ModernDashboardStats | AnalyticsDashboardStats | ExecutiveDashboardStats;

/**
 * Custom hook for fetching dashboard-specific stats
 */
export const useDashboardStats = <T extends DashboardStats>(
  dashboardType: 'classic' | 'modern' | 'analytics' | 'executive',
  refreshInterval: number = REFRESH_INTERVALS.STATS
) => {
  const [stats, setStats] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout>();
  
  // Enforce minimum 30-second interval to avoid excessive API calls
  const safeInterval = Math.max(refreshInterval, REFRESH_INTERVALS.STATS);

  const fetchStats = useCallback(async () => {
    try {
      // Map dashboard type to endpoint
      const endpointMap = {
        classic: API_ENDPOINTS.STATS_CLASSIC,
        modern: API_ENDPOINTS.STATS_MODERN,
        analytics: API_ENDPOINTS.STATS_ANALYTICS,
        executive: API_ENDPOINTS.STATS_EXECUTIVE,
      };
      
      const url = endpointMap[dashboardType];
      const response = await fetch(url);
      const data = await response.json();

      if (data.error) {
        // Check for network loss error
        if (data.error === 'network_lost' && data.redirect) {
          // Show message briefly then redirect
          setError('Network connection lost. Starting setup mode...');
          setStats(null);
          setTimeout(() => {
            window.location.href = data.redirect;
          }, 2000);
        } else {
          setError(data.error);
          setStats(null);
        }
      } else {
        setStats(data as T);
        setError(null);
      }
    } catch (err) {
      setError('Failed to fetch stats');
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [dashboardType]);

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
  };
};
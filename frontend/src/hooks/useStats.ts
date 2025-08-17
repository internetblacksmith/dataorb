import { useState, useEffect, useCallback, useRef } from 'react';
import { DataOrbStats } from '../types';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../constants';

/**
 * Custom hook for fetching and managing stats
 */
export const useStats = (refreshInterval: number = REFRESH_INTERVALS.STATS, layout?: string) => {
  const [stats, setStats] = useState<DataOrbStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout>();
  
  // Enforce minimum 30-second interval to avoid excessive API calls
  const safeInterval = Math.max(refreshInterval, REFRESH_INTERVALS.STATS);

  const fetchStats = useCallback(async () => {
    try {
      // Add layout parameter if provided
      const url = layout 
        ? `${API_ENDPOINTS.STATS}?layout=${layout}`
        : API_ENDPOINTS.STATS;
      
      const response = await fetch(url);
      const data = await response.json();

      if (data.error) {
        setError(data.error);
        setStats(null);
      } else {
        setStats(data);
        setError(null);
      }
    } catch (err) {
      setError('Failed to fetch stats');
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [layout]);

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
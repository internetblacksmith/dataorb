import { useState, useEffect, useCallback, useRef } from 'react';
import { REFRESH_INTERVALS } from '../constants';
import { handleNetworkError } from '../utils/networkErrorHandler';

export const useDashboardStats = <T>(endpoint: string, refreshInterval: number = REFRESH_INTERVALS.STATS) => {
  const [stats, setStats] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout>();

  const safeInterval = Math.max(refreshInterval, REFRESH_INTERVALS.STATS);

  const fetchStats = useCallback(async () => {
    try {
      const response = await fetch(endpoint);
      const data = await response.json();

      if (data.error) {
        if (!handleNetworkError(data, setError, setStats)) {
          setError(data.error);
          setStats(null);
        }
      } else {
        setStats(data as T);
        setError(null);
      }
    } catch {
      setError('Failed to fetch dashboard stats');
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, [endpoint]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

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

  return { stats, loading, error, refetch: fetchStats };
};

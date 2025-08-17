import { useState, useEffect, useCallback } from 'react';
import { DisplayConfig } from '../types';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../constants';

/**
 * Custom hook for display configuration management
 */
export const useDisplayConfig = () => {
  const [displayConfig, setDisplayConfig] = useState<DisplayConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDisplayConfig = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.DISPLAY_CONFIG);
      
      if (!response.ok) {
        throw new Error('Failed to fetch display config');
      }

      const fullConfig = await response.json();
      const displayData: DisplayConfig = fullConfig.display || {};
      setDisplayConfig(displayData);
      setError(null);
      return displayData;
    } catch (err) {
      setError('Failed to load display configuration');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch on mount
  useEffect(() => {
    fetchDisplayConfig();
  }, [fetchDisplayConfig]);

  // Listen for config changes via BroadcastChannel
  useEffect(() => {
    const channel = new BroadcastChannel('config-updates');
    
    const handleMessage = (event: MessageEvent) => {
      if (event.data.type === 'displayConfigUpdated' && event.data.config) {
        setDisplayConfig(event.data.config);
      }
    };

    channel.addEventListener('message', handleMessage);
    
    return () => {
      channel.removeEventListener('message', handleMessage);
      channel.close();
    };
  }, []);

  const getRefreshInterval = useCallback((): number => {
    // Enforce minimum 30-second interval to avoid excessive API calls
    const configInterval = displayConfig?.refresh_interval || REFRESH_INTERVALS.STATS;
    return Math.max(configInterval, REFRESH_INTERVALS.STATS);
  }, [displayConfig]);

  // Get the metrics for the current layout
  const currentLayout = displayConfig?.layout || 'classic';
  const layoutMetrics = displayConfig?.metrics?.[currentLayout as keyof typeof displayConfig.metrics];

  return {
    displayConfig,
    loading,
    error,
    refetch: fetchDisplayConfig,
    refreshInterval: getRefreshInterval(),
    theme: displayConfig?.theme,
    layout: displayConfig?.layout,
    metrics: layoutMetrics,
    allMetrics: displayConfig?.metrics,
  };
};
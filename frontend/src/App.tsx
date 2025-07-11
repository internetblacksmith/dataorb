import React, { useState, useEffect } from 'react';
import './App.css';

interface PostHogStats {
  events_24h: number;
  unique_users_24h: number;
  page_views_24h: number;
  custom_events_24h: number;
  sessions_24h: number;
  events_1h: number;
  avg_events_per_user: number;
  recent_events: any[];
  last_updated: string;
  error?: string;
}

interface DisplayConfig {
  metrics: {
    top: { type: string; label: string; enabled: boolean };
    left: { type: string; label: string; enabled: boolean };
    right: { type: string; label: string; enabled: boolean };
  };
}

const App: React.FC = () => {
  const [stats, setStats] = useState<PostHogStats | null>(null);
  const [displayConfig, setDisplayConfig] = useState<DisplayConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/stats');
      const data = await response.json();
      
      if (data.error) {
        setError(data.error);
      } else {
        setStats(data);
        setError(null);
      }
    } catch (err) {
      setError('Failed to fetch stats');
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDisplayConfig = async () => {
    try {
      const response = await fetch('/api/admin/config');
      const data = await response.json();
      setDisplayConfig({ metrics: data.display.metrics });
    } catch (err) {
      console.error('Error fetching display config:', err);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchDisplayConfig();
    const interval = setInterval(fetchStats, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const formatTime = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return 'N/A';
    }
  };

  const getMetricValue = (metricType: string): string | number => {
    if (!stats) return 0;
    return (stats as any)[metricType] ?? 0;
  };

  if (loading) {
    return (
      <div className="app loading">
        <div className="loading-spinner"></div>
        <p>Loading PostHog Stats...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="app error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={fetchStats}>
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="circular-container">
        {/* Center logo/title */}
        <div className="center-logo">
          <div className="logo-text">PostHog</div>
          <div className="logo-subtitle">Analytics</div>
        </div>

        {/* Circular stats layout */}
        <div className="circular-stats">
          {displayConfig?.metrics.top.enabled && (
            <div className="stat-circle stat-top">
              <div className="stat-value">{getMetricValue(displayConfig.metrics.top.type)}</div>
              <div className="stat-label">{displayConfig.metrics.top.label}</div>
            </div>
          )}

          {displayConfig?.metrics.left.enabled && (
            <div className="stat-circle stat-left">
              <div className="stat-value">{getMetricValue(displayConfig.metrics.left.type)}</div>
              <div className="stat-label">{displayConfig.metrics.left.label}</div>
            </div>
          )}

          {displayConfig?.metrics.right.enabled && (
            <div className="stat-circle stat-right">
              <div className="stat-value">{getMetricValue(displayConfig.metrics.right.type)}</div>
              <div className="stat-label">{displayConfig.metrics.right.label}</div>
            </div>
          )}
        </div>

        {/* Status and time at bottom */}
        <div className="bottom-info">
          <div className="status-indicator">
            <div className="status-dot active"></div>
            <span>Live</span>
          </div>
          <div className="last-updated">
            {stats?.last_updated ? formatTime(stats.last_updated) : '--:--'}
          </div>
        </div>

        {/* Outer ring decoration */}
        <div className="outer-ring"></div>
      </div>
    </div>
  );
};

export default App;
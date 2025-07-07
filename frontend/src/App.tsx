import React, { useState, useEffect } from 'react';
import './App.css';

interface PostHogStats {
  events_24h: number;
  unique_users_24h: number;
  page_views_24h: number;
  last_updated: string;
  error?: string;
}

const App: React.FC = () => {
  const [stats, setStats] = useState<PostHogStats | null>(null);
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

  useEffect(() => {
    fetchStats();
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
          <div className="stat-circle stat-top">
            <div className="stat-value">{stats?.events_24h || 0}</div>
            <div className="stat-label">Events</div>
          </div>

          <div className="stat-circle stat-left">
            <div className="stat-value">{stats?.unique_users_24h || 0}</div>
            <div className="stat-label">Users</div>
          </div>

          <div className="stat-circle stat-right">
            <div className="stat-value">{stats?.page_views_24h || 0}</div>
            <div className="stat-label">Views</div>
          </div>
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
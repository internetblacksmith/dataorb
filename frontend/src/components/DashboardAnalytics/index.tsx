import React, { useState, useMemo } from 'react';
import {
  useTheme,
  useKeyboardNavigation,
  useNetworkStatus,
  useDisplayConfig,
  useInterval,
  useDashboardStats,
  useThemeData
} from '../../hooks';
import { AnalyticsDashboardStats } from '../../types';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { formatTime, formatDate, formatNumber } from '../../utils';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../../constants';
import './styles.css';

const DashboardAnalytics: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  const urlParams = new URLSearchParams(window.location.search);
  const forceLoading = urlParams.get('loading') === 'true';

  useKeyboardNavigation();
  const { error: networkError } = useNetworkStatus();
  const { theme, refreshInterval } = useDisplayConfig();
  const { stats, loading, error: statsError, refetch } = useDashboardStats<AnalyticsDashboardStats>(
    API_ENDPOINTS.STATS_ANALYTICS,
    refreshInterval
  );
  useTheme(theme);
  const themeData = useThemeData(theme);

  useInterval(() => setCurrentTime(new Date()), REFRESH_INTERVALS.TIME);

  const cardinalMetrics = useMemo(() => {
    const metrics = [];
    if (stats?.top) metrics.push({ position: 'top', ...stats.top });
    if (stats?.right) metrics.push({ position: 'right', ...stats.right });
    if (stats?.bottom) metrics.push({ position: 'bottom', ...stats.bottom });
    if (stats?.left) metrics.push({ position: 'left', ...stats.left });
    return metrics;
  }, [stats?.top, stats?.right, stats?.bottom, stats?.left]);

  const bottomStats = useMemo(() => {
    const items = [];
    if (stats?.stat1) items.push(stats.stat1);
    if (stats?.stat2) items.push(stats.stat2);
    if (stats?.stat3) items.push(stats.stat3);
    return items;
  }, [stats?.stat1, stats?.stat2, stats?.stat3]);

  if (networkError === 'wifi-setup-mode') {
    return (
      <div className="dashboard-analytics">
        <div className="circular-container">
          <ErrorDisplay error={networkError} showRetry={false} />
        </div>
      </div>
    );
  }

  if (loading || forceLoading) {
    return (
      <div className="dashboard-analytics loading">
        <div className="circular-container">
          <div className="loading-animation">
            <div className="loading-circle" />
            <div className="loading-text">Loading Analytics...</div>
          </div>
        </div>
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="dashboard-analytics error">
        <div className="circular-container">
          <ErrorDisplay error={statsError} onRetry={refetch} />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-analytics">
      <div className="circular-container">

        <div className="top-section">
          <div className="brand-area">
            {themeData?.logo ? (
              <img
                className="theme-logo"
                src={`data:image/svg+xml;base64,${btoa(themeData.logo)}`}
                alt="Brand logo"
              />
            ) : (
              <div className="default-brand">
                <span className="brand-text">DataOrb</span>
              </div>
            )}
          </div>
          <div className="time-display">
            <div className="time">{formatTime(currentTime)}</div>
            <div className="date">{formatDate(currentTime)}</div>
          </div>
        </div>

        {stats?.center && (
          <div className="center-circle">
            <div className="primary-metric">
              <div className="metric-value-large">
                {formatNumber(stats.center.value)}
              </div>
              <div className="metric-subtitle">{stats.center.label}</div>
            </div>
          </div>
        )}

        <div className="metrics-grid">
          {cardinalMetrics.map((metric) => (
            <div key={metric.position} className={metric.position}>
              <div className="metric-inner">
                <div className="metric-value">{formatNumber(metric.value)}</div>
                <div className="metric-name">{metric.label}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="bottom-stats">
          {bottomStats.map((stat) => (
            <div key={stat.label} className="stat-item">
              <div className="stat-label">{stat.label}</div>
              <div className="stat-value">{formatNumber(stat.value)}</div>
            </div>
          ))}
        </div>

        <div className="status-bar">
          <div className="status-live">
            <span className="live-dot" />
            <span>{stats?.demo_mode ? 'Demo Mode' : 'Live Data'}</span>
          </div>
          <div className="last-updated">
            {formatDate(currentTime)}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardAnalytics;

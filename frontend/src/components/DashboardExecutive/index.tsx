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
import { ExecutiveDashboardStats } from '../../types';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { formatTime, formatDate, formatNumber } from '../../utils';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../../constants';
import './styles.css';

const DashboardExecutive: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  const urlParams = new URLSearchParams(window.location.search);
  const forceLoading = urlParams.get('loading') === 'true';

  useKeyboardNavigation();
  const { networkStatus, error: networkError } = useNetworkStatus();
  const { theme, refreshInterval } = useDisplayConfig();
  const { stats, loading, error: statsError, refetch } = useDashboardStats<ExecutiveDashboardStats>(
    API_ENDPOINTS.STATS_EXECUTIVE,
    refreshInterval
  );
  useTheme(theme);
  const themeData = useThemeData(theme);

  useInterval(() => setCurrentTime(new Date()), REFRESH_INTERVALS.TIME);

  const primaryMetrics = useMemo(() => {
    const metrics = [];
    if (stats?.north) metrics.push({ position: 'north', ...stats.north });
    if (stats?.east) metrics.push({ position: 'east', ...stats.east });
    if (stats?.south) metrics.push({ position: 'south', ...stats.south });
    if (stats?.west) metrics.push({ position: 'west', ...stats.west });
    return metrics;
  }, [stats?.north, stats?.east, stats?.south, stats?.west]);

  const secondaryMetrics = useMemo(() => {
    const metrics = [];
    if (stats?.northEast) metrics.push({ position: 'northeast', ...stats.northEast });
    if (stats?.southEast) metrics.push({ position: 'southeast', ...stats.southEast });
    if (stats?.southWest) metrics.push({ position: 'southwest', ...stats.southWest });
    if (stats?.northWest) metrics.push({ position: 'northwest', ...stats.northWest });
    return metrics;
  }, [stats?.northEast, stats?.southEast, stats?.southWest, stats?.northWest]);

  if (networkError === 'wifi-setup-mode') {
    return (
      <div className="dashboard-executive">
        <ErrorDisplay error={networkError} showRetry={false} />
      </div>
    );
  }

  if (loading || forceLoading) {
    return (
      <div className="dashboard-executive">
        <div className="loading-orb">
          <div className="orb-pulse" />
          <div className="loading-text">Initializing Orb...</div>
        </div>
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="dashboard-executive">
        <ErrorDisplay error={statsError} onRetry={refetch} />
      </div>
    );
  }

  return (
    <div className="dashboard-executive">
      <div className="clock-container">
        <div className="time">{formatTime(currentTime)}</div>
      </div>

      <div className="date-container">
        <div className="date">{formatDate(currentTime)}</div>
      </div>

      {stats?.demo_mode && (
        <div className="demo-indicator">DEMO MODE</div>
      )}

      <div className="orb-container">
        <div className="orbital-decoration">
          <div className="orbit orbit-1" />
          <div className="orbit orbit-2" />
          <div className="orbit orbit-3" />
        </div>

        <div className="center-brand">
          {themeData?.logo ? (
            <img
              className="theme-logo"
              src={`data:image/svg+xml;base64,${btoa(themeData.logo)}`}
              alt="Brand logo"
            />
          ) : (
            <div className="brand-name">DATAORB</div>
          )}
        </div>

        <div className="metrics-ring primary">
          {primaryMetrics.map((metric) => (
            <div key={metric.position} className={`metric-card ${metric.position}`}>
              <div className="metric-value">{formatNumber(metric.value)}</div>
              <div className="metric-label">{metric.label}</div>
            </div>
          ))}
        </div>

        <div className="metrics-ring secondary">
          {secondaryMetrics.map((metric) => (
            <div key={metric.position} className={`metric-mini ${metric.position}`}>
              <div className="mini-value">{formatNumber(metric.value)}</div>
              <div className="mini-label">{metric.label}</div>
            </div>
          ))}
        </div>

      </div>

      <div className="status-bar">
        <div className="status-item">
          <span className={`status-dot ${stats ? 'active' : ''}`} />
          <span className="status-label">Status:</span>
          <span className="status-value">{stats ? 'Online' : 'Offline'}</span>
        </div>
        <div className="status-item">
          <span className="status-label">Network:</span>
          <span className="status-value">{networkStatus?.ssid || 'Unknown'}</span>
        </div>
      </div>

      <div className="keyboard-hint">
        Ctrl+Alt+[1-5] to switch views
      </div>
    </div>
  );
};

export default DashboardExecutive;

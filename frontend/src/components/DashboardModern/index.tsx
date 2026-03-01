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
import { ModernDashboardStats } from '../../types';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { formatTime, formatDate, formatNumber } from '../../utils';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../../constants';
import './styles.css';

const DashboardModern: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  const urlParams = new URLSearchParams(window.location.search);
  const forceLoading = urlParams.get('loading') === 'true';

  useKeyboardNavigation();
  const { networkStatus, error: networkError } = useNetworkStatus();
  const { theme, refreshInterval } = useDisplayConfig();
  const { stats, loading, error: statsError, refetch } = useDashboardStats<ModernDashboardStats>(
    API_ENDPOINTS.STATS_MODERN,
    refreshInterval
  );
  useTheme(theme);
  const themeData = useThemeData(theme);

  useInterval(() => setCurrentTime(new Date()), REFRESH_INTERVALS.TIME);

  const deviceIP = useMemo(
    () => networkStatus?.ip || '[device-ip]',
    [networkStatus]
  );

  const secondaryMetrics = useMemo(() => {
    const metrics = [];
    if (stats?.secondaryLeft) metrics.push({ position: 'left', ...stats.secondaryLeft });
    if (stats?.secondaryRight) metrics.push({ position: 'right', ...stats.secondaryRight });
    return metrics;
  }, [stats?.secondaryLeft, stats?.secondaryRight]);

  const miniStats = useMemo(() => {
    const items = [];
    if (stats?.miniStat1) items.push(stats.miniStat1);
    if (stats?.miniStat2) items.push(stats.miniStat2);
    if (stats?.miniStat3) items.push(stats.miniStat3);
    return items;
  }, [stats?.miniStat1, stats?.miniStat2, stats?.miniStat3]);

  if (networkError === 'wifi-setup-mode') {
    return (
      <div className="dashboard-modern">
        <div className="circular-display">
          <ErrorDisplay error={networkError} showRetry={false} />
        </div>
      </div>
    );
  }

  if (loading || forceLoading) {
    return (
      <div className="dashboard-modern">
        <div className="circular-display">
          <div className="loading-container">
            <div className="loading-ring">
              <div className="loading-segment" />
            </div>
            <p className="loading-text">Initializing Dashboard...</p>
          </div>
        </div>
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="dashboard-modern">
        <div className="circular-display">
          <ErrorDisplay error={statsError} onRetry={refetch} />
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-modern">
      <div className="circular-display">
        <div className="ring-decoration outer" />
        <div className="ring-decoration inner" />

        <div className="header-section">
          <div className="brand">
            {themeData?.logo ? (
              <img
                className="theme-logo"
                src={`data:image/svg+xml;base64,${btoa(themeData.logo)}`}
                alt="Brand logo"
              />
            ) : (
              (!theme || ['dark', 'light'].includes(theme)) && (
                <div className="brand-name">DataOrb</div>
              )
            )}
          </div>
          <div className="header-time">
            <div className="time">{formatTime(currentTime)}</div>
            <div className="date">{formatDate(currentTime)}</div>
          </div>
        </div>

        <div className="metrics-ring">
          {stats?.primary && (
            <div className="metric-primary">
              <div className="metric-value">{formatNumber(stats.primary.value)}</div>
              <div className="metric-label">{stats.primary.label}</div>
            </div>
          )}

          {secondaryMetrics.map((metric) => (
            <div
              key={metric.position}
              className="metric-secondary"
              data-position={metric.position}
            >
              <div className="metric-value">{formatNumber(metric.value)}</div>
              <div className="metric-label">{metric.label}</div>
            </div>
          ))}
        </div>

        <div className="mini-stats-bar">
          {miniStats.map((stat) => (
            <div key={stat.label} className="mini-stat">
              <div className="mini-label">{stat.label}</div>
              <div className="mini-value">{formatNumber(stat.value)}</div>
            </div>
          ))}
        </div>

        <div className="status-footer">
          <div className="status-indicator">
            <span className={`status-dot ${stats ? 'live' : ''}`} />
            <span>{stats?.demo_mode ? 'Demo' : 'Live'}</span>
          </div>
          <div className="last-update">
            {formatTime(currentTime)} • {deviceIP}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardModern;

import React, { useState, useMemo } from 'react';
import {
  useTheme,
  useKeyboardNavigation,
  useNetworkStatus,
  useDisplayConfig,
  useInterval,
  useDashboardStats
} from '../../hooks';
import { ClassicDashboardStats } from '../../types';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { MetricCard } from '../common/MetricCard';
import { formatTime } from '../../utils';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../../constants';
import './styles.css';

const DashboardClassic: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  const urlParams = new URLSearchParams(window.location.search);
  const forceLoading = urlParams.get('loading') === 'true';

  useKeyboardNavigation();
  const { networkStatus, error: networkError } = useNetworkStatus();
  const { displayConfig, theme } = useDisplayConfig();
  const { stats, loading, error: statsError, refetch } = useDashboardStats<ClassicDashboardStats>(
    API_ENDPOINTS.STATS_CLASSIC,
    displayConfig?.refresh_interval
  );
  useTheme(theme);

  useInterval(() => setCurrentTime(new Date()), REFRESH_INTERVALS.TIME);

  const deviceIP = useMemo(
    () => networkStatus?.ip || '[device-ip]',
    [networkStatus]
  );

  if (networkError === 'wifi-setup-mode') {
    return (
      <div className="dashboard-classic">
        <ErrorDisplay error={networkError} showRetry={false} />
      </div>
    );
  }

  if (loading || forceLoading) {
    return (
      <div className="dashboard-classic">
        <div className="circular-container">
          <div className="loading-container">
            <div className="loading-ring">
              <div className="loading-segment" />
            </div>
            <p className="loading-text">Loading DataOrb...</p>
          </div>
        </div>
      </div>
    );
  }

  if (statsError) {
    return (
      <div className="dashboard-classic">
        <ErrorDisplay error={statsError} onRetry={refetch} />
      </div>
    );
  }

  return (
    <div className="dashboard-classic">
      <div className="circular-container">
        <div className="center-logo">
          <div className="logo-text">DataOrb</div>
          <div className="logo-subtitle">ANALYTICS</div>
        </div>

        <div className="circular-stats">
          {stats?.top && (
            <MetricCard
              value={stats.top.value}
              label={stats.top.label}
              position="top"
              size="medium"
            />
          )}
          {stats?.left && (
            <MetricCard
              value={stats.left.value}
              label={stats.left.label}
              position="left"
              size="medium"
            />
          )}
          {stats?.right && (
            <MetricCard
              value={stats.right.value}
              label={stats.right.label}
              position="right"
              size="medium"
            />
          )}
        </div>

        <div className="bottom-info">
          <div className="status-indicator">
            <span className={`status-dot ${stats ? 'active' : ''}`}></span>
            <span>{stats?.demo_mode ? 'Demo Mode' : 'Live Data'}</span>
          </div>
          <div className="last-updated">
            {formatTime(currentTime)} • {deviceIP}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardClassic;

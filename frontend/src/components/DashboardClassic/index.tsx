import React, { useState, useMemo } from 'react';
import {
  useTheme,
  useKeyboardNavigation,
  useNetworkStatus,
  useDisplayConfig,
  useInterval,
  useClassicDashboard
} from '../../hooks';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { MetricCard } from '../common/MetricCard';
import { formatTime, calculateMockTrend } from '../../utils';
import { REFRESH_INTERVALS } from '../../constants';
import './styles.css';
import '../../themes.css';

const DashboardClassic: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());

  // Custom hooks
  useKeyboardNavigation();
  const { networkStatus, error: networkError } = useNetworkStatus();
  const { displayConfig, theme } = useDisplayConfig();
  const { 
    stats, 
    loading, 
    error: statsError, 
    refetch,
    topMetric: topMetricData,
    leftMetric: leftMetricData,
    rightMetric: rightMetricData,
    demoMode,
    deviceIp
  } = useClassicDashboard(displayConfig?.refresh_interval);
  useTheme(theme);

  // Update time every second
  useInterval(() => setCurrentTime(new Date()), REFRESH_INTERVALS.TIME);

  // Memoized values
  const deviceIP = useMemo(() => deviceIp || networkStatus?.ip || '[device-ip]', [deviceIp, networkStatus]);

  // Get metrics with trends
  const topMetric = useMemo(() => topMetricData ? {
    ...topMetricData,
    trend: calculateMockTrend()
  } : null, [topMetricData]);

  const leftMetric = useMemo(() => leftMetricData ? {
    ...leftMetricData,
    trend: calculateMockTrend()
  } : null, [leftMetricData]);

  const rightMetric = useMemo(() => rightMetricData ? {
    ...rightMetricData,
    trend: calculateMockTrend()
  } : null, [rightMetricData]);

  // Handle WiFi setup mode
  if (networkError === 'wifi-setup-mode') {
    return (
      <div className="dashboard-classic">
        <ErrorDisplay error={networkError} showRetry={false} />
      </div>
    );
  }

  // Loading state
  if (loading) {
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

  // Error state
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
          {topMetric && (
            <MetricCard
              value={topMetric.value}
              label={topMetric.label}
              trend={topMetric.trend}
              position="top"
              size="medium"
            />
          )}
          {leftMetric && (
            <MetricCard
              value={leftMetric.value}
              label={leftMetric.label}
              trend={leftMetric.trend}
              position="left"
              size="medium"
            />
          )}
          {rightMetric && (
            <MetricCard
              value={rightMetric.value}
              label={rightMetric.label}
              trend={rightMetric.trend}
              position="right"
              size="medium"
            />
          )}
        </div>

        <div className="bottom-info">
          <div className="status-indicator">
            <span className={`status-dot ${stats ? 'active' : ''}`}></span>
            <span>{demoMode ? 'Demo Mode' : 'Live Data'}</span>
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

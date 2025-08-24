import React, { useState, useMemo } from 'react';
import {
  useTheme,
  useKeyboardNavigation,
  useNetworkStatus,
  useDisplayConfig,
  useInterval,
  useAnalyticsDashboard
} from '../../hooks';
import { ErrorDisplay } from '../common/ErrorDisplay';
import {
  formatTime,
  formatDate,
  formatNumber,
  calculateMockTrend,
  formatPercentage,
  getTrendIcon
} from '../../utils';
import { REFRESH_INTERVALS, API_ENDPOINTS } from '../../constants';
import { Theme } from '../../types';
import './styles.css';
import '../../themes.css';

const DashboardAnalytics: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [themeData, setThemeData] = useState<Theme | null>(null);

  // Check for loading parameter in URL
  const urlParams = new URLSearchParams(window.location.search);
  const forceLoading = urlParams.get('loading') === 'true';

  // Custom hooks
  useKeyboardNavigation();
  const { error: networkError } = useNetworkStatus();
  const { theme, refreshInterval } = useDisplayConfig();
  const { 
    loading, 
    error: statsError, 
    refetch,
    centerMetric,
    topMetric,
    leftMetric,
    rightMetric,
    bottomMetric,
    stat1,
    stat2,
    stat3,
    demoMode
  } = useAnalyticsDashboard(refreshInterval);
  useTheme(theme);

  // Update time every second
  useInterval(() => setCurrentTime(new Date()), REFRESH_INTERVALS.TIME);

  // Load theme data for logo
  React.useEffect(() => {
    // Check for embedded theme data first
    if ((window as any).__INITIAL_DATA__?.theme) {
      setThemeData((window as any).__INITIAL_DATA__.theme);
      // Clear the initial data after using it
      delete (window as any).__INITIAL_DATA__.theme;
      return;
    }
    
    const loadThemeData = async () => {
      if (!theme || ['dark', 'light'].includes(theme)) {
        setThemeData(null);
        return;
      }

      try {
        const response = await fetch(API_ENDPOINTS.THEME_BY_ID(theme));
        if (response.ok) {
          const data = await response.json();
          setThemeData(data);
        }
      } catch {
        // Silently fail
      }
    };

    loadThemeData();
  }, [theme]);

  // Memoized metrics with trends
  const centerMetricWithTrend = useMemo(() => {
    if (!centerMetric) return null;
    return {
      ...centerMetric,
      trend: calculateMockTrend(),
    };
  }, [centerMetric]);

  const cardinalMetrics = useMemo(() => {
    const metrics = [];
    
    if (topMetric) {
      metrics.push({
        position: 'top',
        ...topMetric,
        trend: calculateMockTrend(),
      });
    }
    if (rightMetric) {
      metrics.push({
        position: 'right',
        ...rightMetric,
        trend: calculateMockTrend(),
      });
    }
    if (bottomMetric) {
      metrics.push({
        position: 'bottom',
        ...bottomMetric,
        trend: calculateMockTrend(),
      });
    }
    if (leftMetric) {
      metrics.push({
        position: 'left',
        ...leftMetric,
        trend: calculateMockTrend(),
      });
    }
    
    return metrics;
  }, [topMetric, rightMetric, bottomMetric, leftMetric]);

  const bottomStats = useMemo(() => {
    const statsArray = [];
    if (stat1) statsArray.push(stat1);
    if (stat2) statsArray.push(stat2);
    if (stat3) statsArray.push(stat3);
    return statsArray;
  }, [stat1, stat2, stat3]);

  // WiFi setup mode
  if (networkError === 'wifi-setup-mode') {
    return (
      <div className="dashboard-analytics">
        <div className="circular-container">
          <ErrorDisplay error={networkError} showRetry={false} />
        </div>
      </div>
    );
  }

  // Loading state (or forced loading for testing)
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

  // Error state
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

        {/* Top Section */}
        <div className="top-section">
          <div className="brand-area">
            {themeData?.logo ? (
              <div
                className="theme-logo"
                dangerouslySetInnerHTML={{ __html: themeData.logo }}
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

        {/* Center Circle - Primary Metric */}
        {centerMetricWithTrend && (
          <div className="center-circle">
            <div className="primary-metric">
              <div className="metric-value-large">
                {formatNumber(centerMetricWithTrend.value)}
              </div>
              <div className="metric-subtitle">{centerMetricWithTrend.label}</div>
              {centerMetricWithTrend.trend !== undefined && (
                <div className={`trend-indicator ${centerMetricWithTrend.trend > 0 ? 'positive' : 'negative'}`}>
                  <span className="trend-arrow">{getTrendIcon(centerMetricWithTrend.trend)}</span>
                  <span>{formatPercentage(Math.abs(centerMetricWithTrend.trend))}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Metrics Grid */}
        <div className="metrics-grid">
          {cardinalMetrics.map((metric) => metric && (
            <div key={metric.position} className={metric.position}>
              <div className="metric-inner">
                <div className="metric-value">{formatNumber(metric.value)}</div>
                <div className="metric-name">{metric.label}</div>
                {metric.trend !== undefined && (
                  <div className={`metric-trend ${metric.trend > 0 ? 'up' : 'down'}`}>
                    {metric.trend > 0 ? '+' : ''}{formatPercentage(metric.trend)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Bottom Stats */}
        <div className="bottom-stats">
          {bottomStats.map((stat) => stat && (
            <div key={stat.label} className="stat-item">
              <div className="stat-label">{stat.label}</div>
              <div className="stat-value">{formatNumber(stat.value)}</div>
            </div>
          ))}
        </div>

        {/* Status Bar */}
        <div className="status-bar">
          <div className="status-live">
            <span className="live-dot" />
            <span>{demoMode ? 'Demo Mode' : 'Live Data'}</span>
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

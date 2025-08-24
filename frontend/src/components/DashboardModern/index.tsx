import React, { useState, useMemo } from 'react';
import { 
  useTheme, 
  useKeyboardNavigation, 
  useNetworkStatus, 
  useDisplayConfig,
  useInterval,
  useModernDashboard
} from '../../hooks';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { 
  formatTime, 
  formatDate, 
  formatNumber, 
  calculateMockTrend,
  formatPercentage
} from '../../utils';
import { API_ENDPOINTS, REFRESH_INTERVALS } from '../../constants';
import './styles.css';
import '../../themes.css';

const DashboardModern: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [themeData, setThemeData] = useState<any>(null);
  
  // Check for loading parameter in URL
  const urlParams = new URLSearchParams(window.location.search);
  const forceLoading = urlParams.get('loading') === 'true';
  
  // Custom hooks
  useKeyboardNavigation();
  const { error: networkError } = useNetworkStatus();
  const { theme, refreshInterval } = useDisplayConfig();
  const { 
    stats, 
    loading, 
    error: statsError, 
    refetch,
    primaryMetric: primaryMetricData,
    secondaryLeftMetric: secondaryLeftData,
    secondaryRightMetric: secondaryRightData,
    miniStat1,
    miniStat2,
    miniStat3,
    demoMode,
    lastUpdated
  } = useModernDashboard(refreshInterval);
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

  // Memoized metric data with trends
  const primaryMetric = useMemo(() => {
    if (!primaryMetricData) return null;
    return {
      ...primaryMetricData,
      trend: calculateMockTrend(),
    };
  }, [primaryMetricData]);

  const secondaryMetrics = useMemo(() => {
    const metrics = [];
    if (secondaryLeftData) {
      metrics.push({
        position: 'left',
        ...secondaryLeftData,
        trend: calculateMockTrend(),
      });
    }
    if (secondaryRightData) {
      metrics.push({
        position: 'right',
        ...secondaryRightData,
        trend: calculateMockTrend(),
      });
    }
    return metrics;
  }, [secondaryLeftData, secondaryRightData]);

  // Additional metrics for mini stats bar
  const miniStats = useMemo(() => {
    const stats = [];
    if (miniStat1) stats.push(miniStat1);
    if (miniStat2) stats.push(miniStat2);
    if (miniStat3) stats.push(miniStat3);
    return stats;
  }, [miniStat1, miniStat2, miniStat3]);

  // WiFi setup mode
  if (networkError === 'wifi-setup-mode') {
    return (
      <div className="dashboard-modern">
        <div className="circular-display">
          <ErrorDisplay error={networkError} showRetry={false} />
        </div>
      </div>
    );
  }

  // Loading state (or forced loading for testing)
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

  // Error state
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

        {/* Header Section */}
        <div className="header-section">
          <div className="brand">
            {themeData?.logo ? (
              <div 
                className="theme-logo"
                dangerouslySetInnerHTML={{ __html: themeData.logo }}
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

        {/* Main Metrics Ring */}
        <div className="metrics-ring">
          {/* Primary Metric - Center */}
          {primaryMetric && (
            <div className="metric-primary">
              <div className="metric-value">{formatNumber(primaryMetric.value)}</div>
              <div className="metric-label">{primaryMetric.label}</div>
              {primaryMetric.trend !== undefined && (
                <div className={`metric-trend ${primaryMetric.trend > 0 ? 'up' : 'down'}`}>
                  <span className="trend-icon">{primaryMetric.trend > 0 ? '+' : '-'}</span>
                  <span>{formatPercentage(Math.abs(primaryMetric.trend))}</span>
                </div>
              )}
            </div>
          )}

          {/* Secondary Metrics */}
          {secondaryMetrics.map((metric) => metric && (
            <div 
              key={metric.position}
              className="metric-secondary"
              data-position={metric.position === 'left' ? 'left' : 'right'}
            >
              <div className="metric-value">{formatNumber(metric.value)}</div>
              <div className="metric-label">{metric.label}</div>
              {metric.trend !== undefined && (
                <div className={`metric-trend-mini ${metric.trend > 0 ? 'up' : 'down'}`}>
                  {metric.trend > 0 ? '+' : ''}{formatPercentage(metric.trend)}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Mini Stats Bar */}
        <div className="mini-stats-bar">
          {miniStats.map((stat) => stat && (
            <div key={stat.label} className="mini-stat">
              <div className="mini-label">{stat.label}</div>
              <div className="mini-value">{formatNumber(stat.value)}</div>
            </div>
          ))}
        </div>

        {/* Status Footer */}
        <div className="status-footer">
          <div className="status-indicator">
            <span className={`status-dot ${stats ? 'live' : ''}`} />
            <span>{demoMode ? 'Demo' : 'Live'}</span>
          </div>
          <div className="last-update">
            Updated {new Date(lastUpdated || Date.now()).toLocaleTimeString()}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardModern;
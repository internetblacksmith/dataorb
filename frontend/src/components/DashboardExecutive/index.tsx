import React, { useState, useMemo } from 'react';
import { 
  useTheme, 
  useKeyboardNavigation, 
  useNetworkStatus, 
  useDisplayConfig,
  useInterval,
  useExecutiveDashboard
} from '../../hooks';
import { ErrorDisplay } from '../common/ErrorDisplay';
import { 
  formatTime, 
  formatDate, 
  formatNumber, 
  calculateMockTrend,
  formatPercentage
} from '../../utils';
import { REFRESH_INTERVALS, API_ENDPOINTS } from '../../constants';
import { Theme } from '../../types';
import './styles.css';
import '../../themes.css';

const DashboardExecutive: React.FC = () => {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [themeData, setThemeData] = useState<Theme | null>(null);
  
  // Custom hooks
  useKeyboardNavigation();
  const { networkStatus, error: networkError } = useNetworkStatus();
  const { theme, refreshInterval } = useDisplayConfig();
  const { 
    stats, 
    loading, 
    error: statsError, 
    refetch,
    northMetric,
    eastMetric,
    southMetric,
    westMetric,
    northEastMetric,
    southEastMetric,
    southWestMetric,
    northWestMetric,
    demoMode
  } = useExecutiveDashboard(refreshInterval);
  useTheme(theme);

  // Update time every second
  useInterval(() => setCurrentTime(new Date()), REFRESH_INTERVALS.TIME);

  // Load theme data for logo
  React.useEffect(() => {
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

  // Memoized primary metrics
  const primaryMetrics = useMemo(() => {
    const metrics = [];
    
    if (northMetric) {
      metrics.push({
        position: 'north',
        ...northMetric,
        trend: calculateMockTrend(),
      });
    }
    if (eastMetric) {
      metrics.push({
        position: 'east',
        ...eastMetric,
        trend: calculateMockTrend(),
      });
    }
    if (southMetric) {
      metrics.push({
        position: 'south',
        ...southMetric,
        trend: calculateMockTrend(),
      });
    }
    if (westMetric) {
      metrics.push({
        position: 'west',
        ...westMetric,
        trend: calculateMockTrend(),
      });
    }
    
    return metrics;
  }, [northMetric, eastMetric, southMetric, westMetric]);

  // Memoized secondary metrics (diagonal positions)
  const secondaryMetrics = useMemo(() => {
    const metrics = [];
    
    if (northEastMetric) {
      metrics.push({
        position: 'northeast',
        ...northEastMetric,
      });
    }
    if (southEastMetric) {
      metrics.push({
        position: 'southeast',
        ...southEastMetric,
      });
    }
    if (southWestMetric) {
      metrics.push({
        position: 'southwest',
        ...southWestMetric,
      });
    }
    if (northWestMetric) {
      metrics.push({
        position: 'northwest',
        ...northWestMetric,
      });
    }
    
    return metrics;
  }, [northEastMetric, southEastMetric, southWestMetric, northWestMetric]);


  // WiFi setup mode
  if (networkError === 'wifi-setup-mode') {
    return (
      <div className="dashboard-executive">
        <ErrorDisplay error={networkError} showRetry={false} />
      </div>
    );
  }

  // Loading state
  if (loading) {
    return (
      <div className="dashboard-executive">
        <div className="loading-orb">
          <div className="orb-pulse" />
          <div className="loading-text">Initializing Orb...</div>
        </div>
      </div>
    );
  }

  // Error state
  if (statsError) {
    return (
      <div className="dashboard-executive">
        <ErrorDisplay error={statsError} onRetry={refetch} />
      </div>
    );
  }

  return (
    <div className="dashboard-executive">
      {/* Time Display - Above Logo */}
      <div className="clock-container">
        <div className="time">{formatTime(currentTime)}</div>
      </div>
      
      {/* Date Display - Below Logo */}
      <div className="date-container">
        <div className="date">{formatDate(currentTime)}</div>
      </div>

      {demoMode && (
        <div className="demo-indicator">DEMO MODE</div>
      )}

      {/* Main Orb Container */}
      <div className="orb-container">
        {/* Orbital Decorations */}
        <div className="orbital-decoration">
          <div className="orbit orbit-1" />
          <div className="orbit orbit-2" />
          <div className="orbit orbit-3" />
        </div>

        {/* Center Brand */}
        <div className="center-brand">
          {themeData?.logo ? (
            <div 
              className="theme-logo"
              dangerouslySetInnerHTML={{ __html: themeData.logo }}
            />
          ) : (
            <div className="brand-name">DATAORB</div>
          )}
        </div>

        {/* Primary Metrics Ring */}
        <div className="metrics-ring primary">
          {primaryMetrics.map((metric) => metric && (
            <div key={metric.position} className={`metric-card ${metric.position}`}>
              <div className="metric-value">{formatNumber(metric.value)}</div>
              <div className="metric-label">{metric.label}</div>
              {metric.trend !== undefined && (
                <div className={`metric-trend ${metric.trend > 0 ? 'up' : 'down'}`}>
                  {metric.trend > 0 ? '↑' : '↓'} {formatPercentage(Math.abs(metric.trend))}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Secondary Metrics Ring */}
        <div className="metrics-ring secondary">
          {secondaryMetrics.map((metric) => (
            <div key={metric.position} className={`metric-mini ${metric.position}`}>
              <div className="mini-value">{formatNumber(metric.value)}</div>
              <div className="mini-label">{metric.label}</div>
            </div>
          ))}
        </div>

      </div>

      {/* Status Bar */}
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

      {/* Keyboard Hint */}
      <div className="keyboard-hint">
        Ctrl+Alt+[1-5] to switch views
      </div>
    </div>
  );
};

export default DashboardExecutive;
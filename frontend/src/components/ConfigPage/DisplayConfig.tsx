import React from 'react';
import { DeviceConfig, AvailableMetric } from '../../types';
import { DASHBOARD_LAYOUTS } from '../../constants';

interface DisplayConfigProps {
  config: DeviceConfig;
  availableMetrics: AvailableMetric[];
  onChange: (updates: Partial<DeviceConfig>) => void;
}

export const DisplayConfig: React.FC<DisplayConfigProps> = React.memo(({ 
  config, 
  availableMetrics, 
  onChange 
}) => {
  const handleMetricChange = (
    position: string,
    field: 'enabled' | 'type' | 'label',
    value: any
  ) => {
    const currentLayout = config.display?.layout || 'classic';
    const currentMetrics = config.display?.metrics || {};
    const layoutMetrics = (currentMetrics as any)[currentLayout] || {};
    
    onChange({
      display: {
        ...config.display,
        metrics: {
          ...currentMetrics,
          [currentLayout]: {
            ...layoutMetrics,
            [position]: {
              ...layoutMetrics[position],
              [field]: value,
            },
          },
        },
      },
    });
  };

  const handleRefreshIntervalChange = (value: number) => {
    onChange({
      display: {
        ...config.display,
        refresh_interval: value * 1000, // Convert to milliseconds
      },
    });
  };

  const handleScreensaverTimeoutChange = (value: number) => {
    onChange({
      display: {
        ...config.display,
        screensaver_timeout: value,
      },
    });
  };

  const handleLayoutChange = (layout: string) => {
    onChange({
      display: {
        ...config.display,
        layout,
      },
    });
  };

  // Get metric positions based on selected layout
  const getMetricPositions = (layout: string): Array<{ key: string; label: string }> => {
    switch (layout) {
      case 'classic':
        return [
          { key: 'top', label: 'Top' },
          { key: 'left', label: 'Left' },
          { key: 'right', label: 'Right' },
        ];
      case 'modern':
        return [
          { key: 'top', label: 'Primary Metric' },
          { key: 'left', label: 'Secondary Left' },
          { key: 'right', label: 'Secondary Right' },
          { key: 'mini1', label: 'Mini Stat 1' },
          { key: 'mini2', label: 'Mini Stat 2' },
          { key: 'mini3', label: 'Mini Stat 3' },
        ];
      case 'analytics':
        return [
          { key: 'center', label: 'Center (Primary)' },
          { key: 'top', label: 'Top' },
          { key: 'left', label: 'Left' },
          { key: 'right', label: 'Right' },
          { key: 'bottom', label: 'Bottom' },
          { key: 'stat1', label: 'Bottom Bar - Stat 1' },
          { key: 'stat2', label: 'Bottom Bar - Stat 2' },
          { key: 'stat3', label: 'Bottom Bar - Stat 3' },
        ];
      case 'executive':
        return [
          { key: 'north', label: 'North' },
          { key: 'east', label: 'East' },
          { key: 'south', label: 'South' },
          { key: 'west', label: 'West' },
          { key: 'northeast', label: 'Northeast' },
          { key: 'southeast', label: 'Southeast' },
          { key: 'southwest', label: 'Southwest' },
          { key: 'northwest', label: 'Northwest' },
        ];
      default:
        return [
          { key: 'top', label: 'Top' },
          { key: 'left', label: 'Left' },
          { key: 'right', label: 'Right' },
        ];
    }
  };

  const metricPositions = getMetricPositions(config.display?.layout || 'classic');

  return (
    <div className="config-section">
      <h2>Display Settings</h2>

      {/* Layout Selection */}
      <div className="form-group">
        <label>Dashboard Layout</label>
        <div className="layout-grid">
          {Object.entries(DASHBOARD_LAYOUTS).map(([key, value]) => {
            // Preview image path uses the layout name directly
            const previewImage = `/layout-previews/${value}.png`;
            
            return (
              <div
                key={value}
                className={`layout-card ${config.display?.layout === value ? 'active' : ''}`}
                onClick={() => handleLayoutChange(value)}
              >
                <div className="layout-preview">
                  <img 
                    src={previewImage} 
                    alt={`${value} layout preview`}
                    style={{ 
                      width: '100%', 
                      height: '100%', 
                      objectFit: 'cover',
                      borderRadius: '4px'
                    }}
                  />
                </div>
                <h5>{key.charAt(0).toUpperCase() + key.slice(1).toLowerCase()}</h5>
                <p>{getLayoutDescription(value)}</p>
                {config.display?.layout === value && (
                  <div className="selected-badge">Selected</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Refresh Interval */}
      <div className="form-group">
        <label htmlFor="refresh-interval">
          Refresh Interval: {(config.display?.refresh_interval || 30000) / 1000}s
        </label>
        <input
          id="refresh-interval"
          type="range"
          min="10"
          max="300"
          step="10"
          value={(config.display?.refresh_interval || 30000) / 1000}
          onChange={(e) => handleRefreshIntervalChange(Number(e.target.value))}
        />
      </div>

      {/* Screensaver Timeout */}
      <div className="form-group">
        <label htmlFor="screensaver-timeout">
          Screen Timeout: {config.display?.screensaver_timeout === 0 ? 'Never' : `${config.display?.screensaver_timeout || 0} minutes`}
        </label>
        <select
          id="screensaver-timeout"
          value={config.display?.screensaver_timeout || 0}
          onChange={(e) => handleScreensaverTimeoutChange(Number(e.target.value))}
        >
          <option value={0}>Never (Screen always on)</option>
          <option value={1}>1 minute</option>
          <option value={2}>2 minutes</option>
          <option value={5}>5 minutes</option>
          <option value={10}>10 minutes</option>
          <option value={15}>15 minutes</option>
          <option value={30}>30 minutes</option>
          <option value={60}>1 hour</option>
          <option value={120}>2 hours</option>
        </select>
        <small>How long before the screen turns off when idle</small>
      </div>

      {/* Dashboard Metrics */}
      <h3>Dashboard Metrics for {config.display?.layout?.charAt(0).toUpperCase()}{config.display?.layout?.slice(1)} Layout</h3>
      <div className="metrics-grid">
        {metricPositions.map(({ key: position, label: posLabel }) => {
          const currentLayout = config.display?.layout || 'classic';
          const layoutMetrics = (config.display?.metrics as any)?.[currentLayout] || {};
          const metricConfig = layoutMetrics[position];
          
          return (
            <div key={position} className="metric-config-group compact">
              <h4>{posLabel}</h4>
              
              <div className="form-group compact">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={metricConfig?.enabled ?? true}
                    onChange={(e) => handleMetricChange(position, 'enabled', e.target.checked)}
                  />
                  <span>Enable</span>
                </label>
              </div>

              {(metricConfig?.enabled ?? true) && (
                <>
                  <div className="form-group compact">
                    <label>Type</label>
                    <select
                      value={metricConfig?.type || 'events_24h'}
                      onChange={(e) => handleMetricChange(position, 'type', e.target.value)}
                    >
                      {(availableMetrics || []).map((metric) => (
                        <option key={metric.id} value={metric.id}>
                          {metric.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group compact">
                    <label>Label</label>
                    <input
                      type="text"
                      value={metricConfig?.label || ''}
                      onChange={(e) => handleMetricChange(position, 'label', e.target.value)}
                      placeholder="Auto"
                    />
                  </div>
                </>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
});

function getLayoutDescription(layout: string): string {
  const descriptions: Record<string, string> = {
    classic: 'Classic circular design with three metrics',
    modern: 'Modern ring layout with mini stats',
    analytics: 'Cardinal grid with center focus',
    executive: 'Orbital design with activity indicators',
  };
  return descriptions[layout] || 'Custom layout';
}

DisplayConfig.displayName = 'DisplayConfig';
import React, { useState, useEffect } from 'react';
import './ConfigPage.css';
import './themes.css';

interface DeviceConfig {
  posthog: {
    api_key: string;
    project_id: string;
    host: string;
  };
  display: {
    refresh_interval: number;
    theme: string;
    brightness: number;
    rotation: number;
    screensaver_timeout: number;
    metrics: {
      top: { type: string; label: string; enabled: boolean };
      left: { type: string; label: string; enabled: boolean };
      right: { type: string; label: string; enabled: boolean };
    };
  };
  network: {
    wifi_ssid: string;
    wifi_password: string;
    static_ip: string;
    use_dhcp: boolean;
  };
  advanced: {
    debug_mode: boolean;
    log_level: string;
    auto_update: boolean;
    backup_enabled: boolean;
  };
  ota: {
    enabled: boolean;
    branch: string;
    check_on_boot: boolean;
    auto_pull: boolean;
    last_update: string | null;
    last_check: string | null;
  };
}

interface AvailableMetrics {
  [key: string]: {
    label: string;
    description: string;
  };
}

interface OTAStatus {
  enabled: boolean;
  current_branch: string;
  current_commit: string;
  target_branch: string;
  available_branches: string[];
  auto_pull: boolean;
  check_on_boot: boolean;
  last_update: string | null;
  last_check: string | null;
  repo_path: string;
}

const ConfigPage: React.FC = () => {
  const [config, setConfig] = useState<DeviceConfig | null>(null);
  const [otaStatus, setOtaStatus] = useState<OTAStatus | null>(null);
  const [availableMetrics, setAvailableMetrics] = useState<AvailableMetrics>(
    {},
  );
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState(() => {
    // Get initial tab from URL hash or default to 'posthog'
    const hash = window.location.hash.slice(1);
    return hash || 'posthog';
  });
  const [message, setMessage] = useState<{
    type: 'success' | 'error';
    text: string;
  } | null>(null);
  const [testingConnection, setTestingConnection] = useState(false);
  const [checkingUpdates, setCheckingUpdates] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [themes, setThemes] = useState<any[]>([]);
  const [showThemeImport, setShowThemeImport] = useState(false);

  const API_BASE = process.env.REACT_APP_API_URL || '';

  useEffect(() => {
    loadConfig();
    loadOTAStatus();
    loadAvailableMetrics();
    loadThemes();
  }, []);

  // Handle browser back/forward navigation
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1);
      if (hash && ['posthog', 'display', 'network', 'advanced', 'ota'].includes(hash)) {
        setActiveTab(hash);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Apply theme when config changes
  useEffect(() => {
    if (config?.display?.theme) {
      applyTheme(config.display.theme);
    }
  }, [config?.display?.theme]);

  const loadConfig = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/config`);
      const data = await response.json();
      setConfig(data);
    } catch (error) {
      showMessage('error', 'Failed to load configuration');
    } finally {
      setLoading(false);
    }
  };


  const loadOTAStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/admin/ota/status`);
      const data = await response.json();
      setOtaStatus(data);
    } catch (error) {
      console.error('Failed to load OTA status:', error);
    }
  };

  const loadThemes = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/themes`);
      const data = await response.json();
      setThemes(data);
    } catch (error) {
      console.error('Failed to load themes:', error);
    }
  };

  const applyTheme = async (themeId: string) => {
    // If it's a custom theme, fetch its colors
    if (themeId && !['dark', 'light'].includes(themeId)) {
      try {
        const response = await fetch(`${API_BASE}/api/themes/${themeId}`);
        if (response.ok) {
          const themeData = await response.json();
          if (themeData.colors) {
            // Apply custom theme colors as CSS variables
            const root = document.documentElement;
            root.style.setProperty('--bg-gradient', themeData.colors.background);
            root.style.setProperty('--container-bg', themeData.colors.containerBg);
            root.style.setProperty('--text-color', themeData.colors.text);
            root.style.setProperty('--text-secondary', themeData.colors.textSecondary);
            root.style.setProperty('--accent', themeData.colors.accent);
            root.style.setProperty('--accent-secondary', themeData.colors.accentSecondary);
            root.style.setProperty('--border', themeData.colors.border);
            root.style.setProperty('--shadow', themeData.colors.shadow);
            root.style.setProperty('--stat-bg', themeData.colors.statBg);
            root.style.setProperty('--stat-border', themeData.colors.statBorder);
            root.style.setProperty('--stat-value', themeData.colors.statValue);
            root.style.setProperty('--stat-label', themeData.colors.statLabel);
            root.style.setProperty('--status-dot', themeData.colors.statusDot);
            root.style.setProperty('--glow-primary', themeData.colors.glowPrimary);
            root.style.setProperty('--glow-secondary', themeData.colors.glowSecondary);
          }
        }
      } catch (err) {
        console.error('Failed to load custom theme:', err);
      }
    } else {
      // For built-in themes, just set the data-theme attribute
      document.documentElement.setAttribute('data-theme', themeId);
    }
  };

  const exportTheme = async (themeId: string) => {
    try {
      const response = await fetch(`${API_BASE}/api/themes/${themeId}/export`);
      const data = await response.json();
      
      // Create a download link
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `theme-${themeId}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      showMessage('success', 'Theme exported successfully');
    } catch (error) {
      showMessage('error', 'Failed to export theme');
    }
  };

  const importTheme = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const themeData = JSON.parse(text);
      
      const response = await fetch(`${API_BASE}/api/themes/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(themeData),
      });

      const result = await response.json();
      if (result.success) {
        showMessage('success', 'Theme imported successfully');
        loadThemes();
      } else {
        showMessage('error', result.error || 'Failed to import theme');
      }
    } catch (error) {
      showMessage('error', 'Invalid theme file');
    }
  };

  const deleteTheme = async (themeId: string) => {
    if (!window.confirm('Are you sure you want to delete this theme?')) return;

    try {
      const response = await fetch(`${API_BASE}/api/themes/custom/${themeId}`, {
        method: 'DELETE',
      });

      const result = await response.json();
      if (result.success) {
        showMessage('success', 'Theme deleted successfully');
        loadThemes();
      } else {
        showMessage('error', result.error || 'Failed to delete theme');
      }
    } catch (error) {
      showMessage('error', 'Failed to delete theme');
    }
  };

  const loadAvailableMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/metrics/available`);
      const data = await response.json();
      setAvailableMetrics(data);
    } catch (error) {
      console.error('Failed to load available metrics:', error);
      // Set default metrics if API fails
      setAvailableMetrics({
        events_24h: {
          label: "Events (24h)",
          description: "Total events in the last 24 hours"
        },
        unique_users_24h: {
          label: "Users (24h)",
          description: "Unique users in the last 24 hours"
        },
        page_views_24h: {
          label: "Page Views (24h)",
          description: "Page view events in the last 24 hours"
        },
        custom_events_24h: {
          label: "Custom Events (24h)",
          description: "Non-pageview events in the last 24 hours"
        },
        sessions_24h: {
          label: "Sessions (24h)",
          description: "Unique sessions in the last 24 hours"
        },
        events_1h: {
          label: "Events (1h)",
          description: "Events in the last hour"
        },
        avg_events_per_user: {
          label: "Avg Events/User",
          description: "Average events per user in the last 24 hours"
        }
      });
    }
  };

  const saveConfig = async () => {
    if (!config) return;

    setSaving(true);
    try {
      const response = await fetch(`${API_BASE}/api/admin/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      const result = await response.json();
      if (result.success) {
        showMessage('success', 'Configuration saved successfully');
        // Trigger a refresh on the dashboard
        if ('BroadcastChannel' in window) {
          const channel = new BroadcastChannel('posthog_config');
          channel.postMessage({ action: 'reload' });
          channel.close();
        }
        // Also set localStorage for cross-origin fallback
        localStorage.setItem('posthog_config_updated', Date.now().toString());
      } else {
        showMessage('error', result.error || 'Failed to save configuration');
      }
    } catch (error) {
      showMessage('error', 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const testPostHogConnection = async () => {
    if (!config) return;

    setTestingConnection(true);
    try {
      const response = await fetch(
        `${API_BASE}/api/admin/config/validate/posthog`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config.posthog),
        },
      );

      const result = await response.json();
      if (result.valid) {
        showMessage('success', result.message);
      } else {
        showMessage('error', result.error);
      }
    } catch (error) {
      showMessage('error', 'Failed to test connection');
    } finally {
      setTestingConnection(false);
    }
  };

  const resetConfig = async () => {
    if (
      !window.confirm(
        'Are you sure you want to reset all settings to defaults?',
      )
    )
      return;

    try {
      const response = await fetch(`${API_BASE}/api/admin/config/reset`, {
        method: 'POST',
      });

      const result = await response.json();
      if (result.success) {
        showMessage('success', 'Configuration reset to defaults');
        loadConfig();
      } else {
        showMessage('error', result.error || 'Failed to reset configuration');
      }
    } catch (error) {
      showMessage('error', 'Failed to reset configuration');
    }
  };

  const checkForUpdates = async () => {
    setCheckingUpdates(true);
    try {
      const response = await fetch(`${API_BASE}/api/admin/ota/check`);
      const result = await response.json();

      if (result.error) {
        showMessage('error', result.error);
      } else if (result.updates_available) {
        showMessage('success', `${result.commits_behind} updates available`);
      } else {
        showMessage('success', 'No updates available');
      }

      loadOTAStatus();
    } catch (error) {
      showMessage('error', 'Failed to check for updates');
    } finally {
      setCheckingUpdates(false);
    }
  };

  const updateSystem = async () => {
    if (
      !window.confirm(
        'Are you sure you want to update the system? This will restart the application.',
      )
    )
      return;

    setUpdating(true);
    try {
      const response = await fetch(`${API_BASE}/api/admin/ota/update`, {
        method: 'POST',
      });

      const result = await response.json();
      if (result.success) {
        showMessage('success', 'System updated successfully');
        loadOTAStatus();
      } else {
        showMessage('error', result.error || 'Failed to update system');
      }
    } catch (error) {
      showMessage('error', 'Failed to update system');
    } finally {
      setUpdating(false);
    }
  };

  const switchBranch = async (branch: string) => {
    if (
      !window.confirm(
        `Are you sure you want to switch to branch ${branch}? This will restart the application.`,
      )
    )
      return;

    setUpdating(true);
    try {
      const response = await fetch(`${API_BASE}/api/admin/ota/switch-branch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ branch }),
      });

      const result = await response.json();
      if (result.success) {
        showMessage('success', result.message);
        loadOTAStatus();
        loadConfig();
      } else {
        showMessage('error', result.error || 'Failed to switch branch');
      }
    } catch (error) {
      showMessage('error', 'Failed to switch branch');
    } finally {
      setUpdating(false);
    }
  };

  const showMessage = (type: 'success' | 'error', text: string) => {
    setMessage({ type, text });
    setTimeout(() => setMessage(null), 5000);
  };

  const handleTabChange = (tabId: string) => {
    setActiveTab(tabId);
    window.location.hash = tabId;
  };

  const updateConfig = (
    section: keyof DeviceConfig,
    field: string,
    value: any,
  ) => {
    if (!config) return;

    setConfig({
      ...config,
      [section]: {
        ...config[section],
        [field]: value,
      },
    });
  };

  const tabs = [
    { id: 'posthog', label: 'PostHog', icon: '📊' },
    { id: 'display', label: 'Display', icon: '🖥️' },
    { id: 'network', label: 'Network', icon: '🌐' },
    { id: 'advanced', label: 'Advanced', icon: '⚙️' },
    { id: 'ota', label: 'Updates', icon: '🔄' },
  ];

  if (loading) {
    return (
      <div className="config-page loading">
        <div className="loading-spinner"></div>
        <p>Loading configuration...</p>
      </div>
    );
  }

  if (!config) {
    return (
      <div className="config-page error">
        <h2>Error</h2>
        <p>Failed to load configuration</p>
        <button onClick={loadConfig}>Retry</button>
      </div>
    );
  }

  return (
    <div className="config-page">
      <header className="config-header">
        <h1>⚙️ DataOrb Configuration</h1>
        <div className="header-actions">
          <button
            onClick={() => (window.location.href = '/')}
            className="btn-secondary"
          >
            📊 Dashboard
          </button>
          <button
            onClick={resetConfig}
            className="btn-danger"
            title="Reset to defaults"
          >
            🔄 Reset
          </button>
          <button
            onClick={saveConfig}
            disabled={saving}
            className="btn-primary"
          >
            {saving ? '💾 Saving...' : '💾 Save'}
          </button>
        </div>
      </header>

      {message && (
        <div className={`message ${message.type}`}>{message.text}</div>
      )}

      <div className="config-content">
        <nav className="config-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => handleTabChange(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </nav>

        <div className="config-panel">
          {activeTab === 'posthog' && (
            <div className="config-section">
              <h2>PostHog Configuration</h2>
              <div className="form-group">
                <label>API Key</label>
                <input
                  type="password"
                  value={config.posthog.api_key}
                  onChange={(e) =>
                    updateConfig('posthog', 'api_key', e.target.value)
                  }
                  placeholder="Your PostHog API key"
                />
              </div>
              <div className="form-group">
                <label>Project ID</label>
                <input
                  type="text"
                  value={config.posthog.project_id}
                  onChange={(e) =>
                    updateConfig('posthog', 'project_id', e.target.value)
                  }
                  placeholder="Your PostHog project ID"
                />
              </div>
              <div className="form-group">
                <label>PostHog Host</label>
                <select
                  value={
                    config.posthog.host === 'https://app.posthog.com' ||
                    config.posthog.host === 'https://eu.posthog.com'
                      ? config.posthog.host
                      : 'custom'
                  }
                  onChange={(e) => {
                    if (e.target.value === 'custom') {
                      // Don't change the host value, just show the custom input
                      updateConfig('posthog', 'host', config.posthog.host || 'https://');
                    } else {
                      updateConfig('posthog', 'host', e.target.value);
                    }
                  }}
                >
                  <option value="https://app.posthog.com">PostHog Cloud (US)</option>
                  <option value="https://eu.posthog.com">PostHog Cloud (EU)</option>
                  <option value="custom">Self-hosted / Custom</option>
                </select>
              </div>
              {(config.posthog.host !== 'https://app.posthog.com' &&
                config.posthog.host !== 'https://eu.posthog.com') && (
                <div className="form-group">
                  <label>Custom Host URL</label>
                  <input
                    type="url"
                    value={config.posthog.host}
                    onChange={(e) =>
                      updateConfig('posthog', 'host', e.target.value)
                    }
                    placeholder="https://posthog.example.com"
                    required
                  />
                  <small>Enter the URL of your self-hosted PostHog instance</small>
                </div>
              )}
              <button
                onClick={testPostHogConnection}
                disabled={testingConnection}
                className="btn-secondary"
              >
                {testingConnection ? '🔄 Testing...' : '🧪 Test Connection'}
              </button>
            </div>
          )}

          {activeTab === 'display' && (
            <div className="config-section">
              <h2>Display Settings</h2>
              <div className="form-group">
                <label>Refresh Interval (seconds)</label>
                <input
                  type="number"
                  min="5"
                  max="300"
                  value={config.display.refresh_interval}
                  onChange={(e) =>
                    updateConfig(
                      'display',
                      'refresh_interval',
                      parseInt(e.target.value),
                    )
                  }
                />
              </div>
              
              <h3>Theme Settings</h3>
              
              <div className="theme-actions">
                <label className="btn-secondary" style={{ cursor: 'pointer' }}>
                  📤 Import Theme
                  <input
                    type="file"
                    accept=".json"
                    onChange={importTheme}
                    style={{ display: 'none' }}
                  />
                </label>
              </div>

              <div className="theme-list">
                <div className="theme-grid">
                  {themes.map((theme) => (
                    <div 
                      key={theme.id} 
                      className={`theme-card ${config.display.theme === theme.id ? 'active' : ''}`}
                    >
                      <h5>{theme.name} {theme.isCustom && <span className="custom-badge">Custom</span>}</h5>
                      <p>{theme.description}</p>
                      <div className="theme-card-actions">
                        {config.display.theme === theme.id ? (
                          <button
                            className="btn-icon selected"
                            disabled
                          >
                            ✓ Selected
                          </button>
                        ) : (
                          <button
                            onClick={() => updateConfig('display', 'theme', theme.id)}
                            className="btn-icon select"
                          >
                            Select
                          </button>
                        )}
                        <button
                          onClick={() => exportTheme(theme.id)}
                          title="Export theme"
                          className="btn-icon"
                        >
                          📥 Export
                        </button>
                        {theme.isCustom && (
                          <button
                            onClick={() => deleteTheme(theme.id)}
                            title="Delete theme"
                            className="btn-icon delete"
                          >
                            🗑️ Delete
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="form-group" style={{ marginTop: '20px' }}>
                <label>Brightness (%)</label>
                <input
                  type="range"
                  min="10"
                  max="100"
                  value={config.display.brightness}
                  onChange={(e) =>
                    updateConfig(
                      'display',
                      'brightness',
                      parseInt(e.target.value),
                    )
                  }
                />
                <span>{config.display.brightness}%</span>
              </div>
              <div className="form-group">
                <label>Rotation (degrees)</label>
                <select
                  value={config.display.rotation}
                  onChange={(e) =>
                    updateConfig(
                      'display',
                      'rotation',
                      parseInt(e.target.value),
                    )
                  }
                >
                  <option value="0">0°</option>
                  <option value="90">90°</option>
                  <option value="180">180°</option>
                  <option value="270">270°</option>
                </select>
              </div>

              <h3>Dashboard Metrics</h3>
              <p>Configure which metrics are displayed on the dashboard</p>

              {['top', 'left', 'right'].map((position) => (
                <div key={position} className="metric-config-group">
                  <h4>
                    {position.charAt(0).toUpperCase() + position.slice(1)}{' '}
                    Position
                  </h4>
                  <div className="form-group">
                    <label>
                      <input
                        type="checkbox"
                        checked={
                          config.display.metrics[
                            position as keyof typeof config.display.metrics
                          ].enabled
                        }
                        onChange={(e) => {
                          const newMetrics = { ...config.display.metrics };
                          newMetrics[
                            position as keyof typeof newMetrics
                          ].enabled = e.target.checked;
                          updateConfig('display', 'metrics', newMetrics);
                        }}
                      />
                      Enable metric
                    </label>
                  </div>
                  {config.display.metrics[
                    position as keyof typeof config.display.metrics
                  ].enabled && (
                    <>
                      <div className="form-group">
                        <label>Metric Type</label>
                        <select
                          value={
                            config.display.metrics[
                              position as keyof typeof config.display.metrics
                            ].type
                          }
                          onChange={(e) => {
                            const newMetrics = { ...config.display.metrics };
                            const selectedMetric =
                              availableMetrics[e.target.value];
                            newMetrics[position as keyof typeof newMetrics] = {
                              type: e.target.value,
                              label: selectedMetric?.label || e.target.value,
                              enabled: true,
                            };
                            updateConfig('display', 'metrics', newMetrics);
                          }}
                        >
                          {Object.entries(availableMetrics).map(
                            ([key, metric]) => (
                              <option key={key} value={key}>
                                {metric.label}
                              </option>
                            ),
                          )}
                        </select>
                      </div>
                      <div className="form-group">
                        <label>Display Label</label>
                        <input
                          type="text"
                          value={
                            config.display.metrics[
                              position as keyof typeof config.display.metrics
                            ].label
                          }
                          onChange={(e) => {
                            const newMetrics = { ...config.display.metrics };
                            newMetrics[
                              position as keyof typeof newMetrics
                            ].label = e.target.value;
                            updateConfig('display', 'metrics', newMetrics);
                          }}
                          placeholder="Custom label"
                        />
                      </div>
                      <small className="metric-description">
                        {
                          availableMetrics[
                            config.display.metrics[
                              position as keyof typeof config.display.metrics
                            ].type
                          ]?.description
                        }
                      </small>
                    </>
                  )}
                </div>
              ))}
            </div>
          )}

          {activeTab === 'network' && (
            <div className="config-section">
              <h2>Network Settings</h2>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={config.network.use_dhcp}
                    onChange={(e) =>
                      updateConfig('network', 'use_dhcp', e.target.checked)
                    }
                  />
                  Use DHCP (automatic IP)
                </label>
              </div>
              {!config.network.use_dhcp && (
                <div className="form-group">
                  <label>Static IP Address</label>
                  <input
                    type="text"
                    value={config.network.static_ip}
                    onChange={(e) =>
                      updateConfig('network', 'static_ip', e.target.value)
                    }
                    placeholder="192.168.1.100"
                  />
                </div>
              )}
              <div className="form-group">
                <label>WiFi SSID</label>
                <input
                  type="text"
                  value={config.network.wifi_ssid}
                  onChange={(e) =>
                    updateConfig('network', 'wifi_ssid', e.target.value)
                  }
                  placeholder="Your WiFi network name"
                />
              </div>
              <div className="form-group">
                <label>WiFi Password</label>
                <input
                  type="password"
                  value={config.network.wifi_password}
                  onChange={(e) =>
                    updateConfig('network', 'wifi_password', e.target.value)
                  }
                  placeholder="Your WiFi password"
                />
              </div>
            </div>
          )}

          {activeTab === 'advanced' && (
            <div className="config-section">
              <h2>Advanced Settings</h2>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={config.advanced.debug_mode}
                    onChange={(e) =>
                      updateConfig('advanced', 'debug_mode', e.target.checked)
                    }
                  />
                  Debug Mode
                </label>
              </div>
              <div className="form-group">
                <label>Log Level</label>
                <select
                  value={config.advanced.log_level}
                  onChange={(e) =>
                    updateConfig('advanced', 'log_level', e.target.value)
                  }
                >
                  <option value="DEBUG">Debug</option>
                  <option value="INFO">Info</option>
                  <option value="WARNING">Warning</option>
                  <option value="ERROR">Error</option>
                </select>
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={config.advanced.auto_update}
                    onChange={(e) =>
                      updateConfig('advanced', 'auto_update', e.target.checked)
                    }
                  />
                  Auto Update
                </label>
              </div>
              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={config.advanced.backup_enabled}
                    onChange={(e) =>
                      updateConfig(
                        'advanced',
                        'backup_enabled',
                        e.target.checked,
                      )
                    }
                  />
                  Enable Backups
                </label>
              </div>
            </div>
          )}

          {activeTab === 'ota' && (
            <div className="config-section">
              <h2>Over-The-Air Updates</h2>

              {otaStatus && (
                <div className="ota-status">
                  <div className="info-grid">
                    <div className="info-card">
                      <h3>Current Status</h3>
                      <p>
                        <strong>Branch:</strong> {otaStatus.current_branch}
                      </p>
                      <p>
                        <strong>Commit:</strong> {otaStatus.current_commit}
                      </p>
                      <p>
                        <strong>Last Check:</strong>{' '}
                        {otaStatus.last_check
                          ? new Date(otaStatus.last_check).toLocaleString()
                          : 'Never'}
                      </p>
                      <p>
                        <strong>Last Update:</strong>{' '}
                        {otaStatus.last_update
                          ? new Date(otaStatus.last_update).toLocaleString()
                          : 'Never'}
                      </p>
                    </div>

                    <div className="info-card">
                      <h3>Actions</h3>
                      <div className="button-group">
                        <button
                          onClick={checkForUpdates}
                          disabled={checkingUpdates}
                          className="btn-secondary"
                        >
                          {checkingUpdates
                            ? '🔄 Checking...'
                            : '🔍 Check for Updates'}
                        </button>
                        <button
                          onClick={updateSystem}
                          disabled={updating}
                          className="btn-primary"
                        >
                          {updating ? '🔄 Updating...' : '⬆️ Update System'}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={config?.ota?.enabled || false}
                    onChange={(e) =>
                      updateConfig('ota', 'enabled', e.target.checked)
                    }
                  />
                  Enable OTA Updates
                </label>
              </div>

              <div className="form-group">
                <label>Target Branch</label>
                <select
                  value={config?.ota?.branch || 'main'}
                  onChange={(e) => {
                    updateConfig('ota', 'branch', e.target.value);
                    if (e.target.value !== otaStatus?.current_branch) {
                      switchBranch(e.target.value);
                    }
                  }}
                  disabled={updating}
                >
                  {otaStatus?.available_branches?.map((branch) => (
                    <option key={branch} value={branch}>
                      {branch}
                    </option>
                  )) || (
                    <>
                      <option value="main">main</option>
                      <option value="dev">dev</option>
                      <option value="canary">canary</option>
                    </>
                  )}
                </select>
                <small>Current: {otaStatus?.current_branch || 'unknown'}</small>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={config?.ota?.check_on_boot || false}
                    onChange={(e) =>
                      updateConfig('ota', 'check_on_boot', e.target.checked)
                    }
                  />
                  Check for updates on boot
                </label>
              </div>

              <div className="form-group">
                <label>
                  <input
                    type="checkbox"
                    checked={config?.ota?.auto_pull || false}
                    onChange={(e) =>
                      updateConfig('ota', 'auto_pull', e.target.checked)
                    }
                  />
                  Automatically pull updates
                </label>
              </div>

              <div className="form-group">
                <label>Repository Path</label>
                <input
                  type="text"
                  value={otaStatus?.repo_path || ''}
                  readOnly
                  className="readonly"
                />
              </div>
            </div>
          )}

        </div>
      </div>
    </div>
  );
};

export default ConfigPage;

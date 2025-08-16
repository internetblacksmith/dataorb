import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';
import './themes.css';

interface DataOrbStats {
  events_24h: number;
  unique_users_24h: number;
  page_views_24h: number;
  custom_events_24h: number;
  sessions_24h: number;
  events_1h: number;
  avg_events_per_user: number;
  recent_events: any[];
  last_updated: string;
  error?: string;
}

interface DisplayConfig {
  theme?: string;
  metrics: {
    top: { type: string; label: string; enabled: boolean };
    left: { type: string; label: string; enabled: boolean };
    right: { type: string; label: string; enabled: boolean };
  };
}

const App: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DataOrbStats | null>(null);
  const [displayConfig, setDisplayConfig] = useState<DisplayConfig | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deviceIP, setDeviceIP] = useState<string>('[device-ip]');

  const fetchStats = async () => {
    try {
      // First check network status
      const networkResponse = await fetch('/api/network/status');
      if (networkResponse.ok) {
        const networkData = await networkResponse.json();

        // If in AP mode, redirect to setup page
        if (networkData.ap_mode) {
          // Check if we're accessing from the AP network
          const isAPNetwork = window.location.hostname === '192.168.4.1' ||
                            window.location.hostname.startsWith('192.168.4.');
          
          if (isAPNetwork) {
            // Redirect to setup page
            navigate('/setup');
            return;
          }
          
          // If on local display, show WiFi setup message
          const isLocalDisplay =
            window.location.hostname === 'localhost' ||
            window.location.hostname === '127.0.0.1';

          if (isLocalDisplay) {
            setError('wifi-setup-mode');
            setLoading(false);
            return;
          }
        }
      }
    } catch (err) {
      // Network status check failed, continue with normal flow
    }

    try {
      const response = await fetch('/api/stats');
      const data = await response.json();

      if (data.error) {
        setError(data.error);
      } else {
        setStats(data);
        setError(null);
      }
    } catch (err) {
      // Check if we're on local display
      const isLocalDisplay =
        window.location.hostname === 'localhost' ||
        window.location.hostname === '127.0.0.1';

      if (isLocalDisplay) {
        // On local display, any network error means show WiFi setup
        setError('wifi-setup-mode');
      } else {
        setError('Failed to fetch stats');
      }
      // Error is already handled by setting error state
    } finally {
      setLoading(false);
    }
  };

  const applyTheme = async (themeId: string) => {
    // If it's a custom theme, fetch its colors
    if (themeId && !['dark', 'light'].includes(themeId)) {
      try {
        const response = await fetch(`/api/themes/${themeId}`);
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

  const fetchDisplayConfig = async () => {
    try {
      const response = await fetch('/api/admin/config');
      const data = await response.json();
      setDisplayConfig({ 
        theme: data.display?.theme || 'dark',
        metrics: data.display.metrics 
      });

      // Apply theme
      if (data.display?.theme) {
        await applyTheme(data.display.theme);
      }

      // Also set device IP from the same response
      if (data.network?.ip_address) {
        setDeviceIP(data.network.ip_address);
      } else {
        // Try to get IP from window location if not localhost
        const hostname = window.location.hostname;
        if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
          setDeviceIP(hostname);
        }
      }
    } catch (err) {
      // Silently fail - display config is optional
      // But still try to get IP from window location
      const hostname = window.location.hostname;
      if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
        setDeviceIP(hostname);
      }
    }
  };

  useEffect(() => {
    fetchStats();
    fetchDisplayConfig(); // This now also sets device IP

    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchStats();
      fetchDisplayConfig();
    }, 30000);

    // Listen for configuration updates via localStorage
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'posthog_config_updated') {
        // Configuration was updated, reload the page
        window.location.reload();
      }
    };
    window.addEventListener('storage', handleStorageChange);

    // Listen for configuration updates via BroadcastChannel
    let channel: BroadcastChannel | undefined;
    if ('BroadcastChannel' in window) {
      channel = new BroadcastChannel('posthog_config');
      channel.onmessage = (event) => {
        if (event.data?.action === 'reload') {
          // Configuration was updated, reload the page
          window.location.reload();
        }
      };
    }

    // Also check periodically if config was updated (fallback for cross-origin)
    const configCheckInterval = setInterval(() => {
      const lastUpdate = localStorage.getItem('posthog_config_updated');
      const lastCheck = localStorage.getItem('posthog_config_last_check');

      if (
        lastUpdate &&
        lastCheck &&
        parseInt(lastUpdate) > parseInt(lastCheck)
      ) {
        localStorage.setItem('posthog_config_last_check', lastUpdate);
        window.location.reload();
      } else if (lastUpdate && !lastCheck) {
        localStorage.setItem('posthog_config_last_check', lastUpdate);
      }
    }, 5000); // Check every 5 seconds

    return () => {
      clearInterval(interval);
      clearInterval(configCheckInterval);
      window.removeEventListener('storage', handleStorageChange);
      if (channel) {
        channel.close();
      }
    };
  }, []);

  const formatTime = (timestamp: string): string => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return 'N/A';
    }
  };

  const getMetricValue = (metricType: string): string | number => {
    if (!stats) return 0;
    return (stats as any)[metricType] ?? 0;
  };

  if (loading) {
    return (
      <div className="app loading">
        <div className="loading-spinner"></div>
        <p>Loading DataOrb Stats...</p>
      </div>
    );
  }

  if (error) {
    // Check if accessing from localhost (LCD display) or remote (PC)
    const isLocalDisplay =
      window.location.hostname === 'localhost' ||
      window.location.hostname === '127.0.0.1';

    // Auto-redirect only if accessing from remote PC
    if (!isLocalDisplay) {
      if (error.includes('PostHog credentials not configured')) {
        navigate('/config');
        return (
          <div className="app loading">
            <div className="loading-spinner"></div>
            <p>Redirecting to configuration...</p>
          </div>
        );
      }

      if (error.includes('401')) {
        navigate('/config?error=401');
        return (
          <div className="app loading">
            <div className="loading-spinner"></div>
            <p>Authentication error - redirecting to configuration...</p>
          </div>
        );
      }

      if (error.includes('403')) {
        navigate('/config?error=403');
        return (
          <div className="app loading">
            <div className="loading-spinner"></div>
            <p>Permission error - redirecting to configuration...</p>
          </div>
        );
      }
    }

    // Show WiFi setup instructions if in AP mode
    if (error === 'wifi-setup-mode') {
      return (
        <div className="app">
          <div className="circular-container">
            <div
              className="config-message"
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                padding: '20px',
                maxWidth: '85%',
                zIndex: 10,
              }}
            >
              <h2
                style={{
                  color: '#1d4aff',
                  marginBottom: '10px',
                  fontSize: '20px',
                }}
              >
                🌐 DataOrb Setup
              </h2>

              <div
                style={{
                  background: '#1e293b',
                  padding: '10px',
                  borderRadius: '10px',
                  marginBottom: '10px',
                  border: '2px solid #1d4aff',
                }}
              >
                <p
                  style={{
                    fontSize: '13px',
                    marginBottom: '6px',
                    color: '#94a3b8',
                  }}
                >
                  1. Connect to WiFi:
                </p>
                <div
                  style={{
                    fontSize: '18px',
                    fontWeight: 'bold',
                    color: '#fff',
                    marginBottom: '3px',
                  }}
                >
                  📶 DataOrb-Setup
                </div>
                <p style={{ fontSize: '11px', color: '#94a3b8' }}>
                  Pass:{' '}
                  <span style={{ fontFamily: 'monospace', color: '#10b981' }}>
                    dataorb123
                  </span>
                </p>
              </div>

              <div
                style={{
                  background: '#1e293b',
                  padding: '8px',
                  borderRadius: '10px',
                  fontSize: '13px',
                }}
              >
                <p style={{ marginBottom: '3px', color: '#94a3b8' }}>
                  2. Open browser:
                </p>
                <div
                  style={{
                    fontFamily: 'monospace',
                    fontSize: '14px',
                    color: '#10b981',
                  }}
                >
                  192.168.4.1:5000
                </div>
              </div>

              <p
                style={{ fontSize: '10px', color: '#64748b', marginTop: '8px' }}
              >
                No network • AP mode active
              </p>
            </div>
          </div>
        </div>
      );
    }

    // Show configuration message on LCD display
    if (
      error.includes('PostHog credentials not configured') ||
      error.includes('401') ||
      error.includes('403')
    ) {
      return (
        <div className="app">
          <div className="circular-container">
            <div
              className="config-message"
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                textAlign: 'center',
                padding: '20px',
                maxWidth: '80%',
                zIndex: 10,
              }}
            >
              <h2
                style={{
                  color: '#1d4aff',
                  marginBottom: '10px',
                  fontSize: '20px',
                }}
              >
                🌐 DataOrb Setup
              </h2>
              <p style={{ fontSize: '14px', marginBottom: '10px' }}>
                Visit this device's IP from your computer:
              </p>
              <div
                style={{
                  background: '#1e293b',
                  padding: '10px',
                  borderRadius: '8px',
                  fontSize: '16px',
                  fontFamily: 'monospace',
                  marginBottom: '10px',
                  color: '#10b981',
                }}
              >
                {`http://${deviceIP}:5000/config`}
              </div>
              <p style={{ fontSize: '12px', color: '#94a3b8' }}>
                {error.includes('401') && '⚠️ Invalid API key'}
                {error.includes('403') && '⚠️ Permission error'}
                {error.includes('not configured') && '❌ PostHog config needed'}
              </p>
            </div>
          </div>
        </div>
      );
    }

    return (
      <div className="app error">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={fetchStats}>Retry</button>
      </div>
    );
  }

  return (
    <div className="app">
      <div className="circular-container">
        {/* Center logo/title */}
        <div className="center-logo">
          <div className="logo-text">DataOrb</div>
          <div className="logo-subtitle">Analytics</div>
        </div>

        {/* Circular stats layout */}
        <div className="circular-stats">
          {displayConfig?.metrics.top.enabled && (
            <div className="stat-circle stat-top">
              <div className="stat-value">
                {getMetricValue(displayConfig.metrics.top.type)}
              </div>
              <div className="stat-label">
                {displayConfig.metrics.top.label}
              </div>
            </div>
          )}

          {displayConfig?.metrics.left.enabled && (
            <div className="stat-circle stat-left">
              <div className="stat-value">
                {getMetricValue(displayConfig.metrics.left.type)}
              </div>
              <div className="stat-label">
                {displayConfig.metrics.left.label}
              </div>
            </div>
          )}

          {displayConfig?.metrics.right.enabled && (
            <div className="stat-circle stat-right">
              <div className="stat-value">
                {getMetricValue(displayConfig.metrics.right.type)}
              </div>
              <div className="stat-label">
                {displayConfig.metrics.right.label}
              </div>
            </div>
          )}
        </div>

        {/* Status and time at bottom */}
        <div className="bottom-info">
          <div className="status-indicator">
            <div className="status-dot active"></div>
            <span>Live</span>
          </div>
          <div className="last-updated">
            {stats?.last_updated ? formatTime(stats.last_updated) : '--:--'}
          </div>
        </div>

        {/* Outer ring decoration */}
        <div className="outer-ring"></div>
      </div>
    </div>
  );
};

export default App;

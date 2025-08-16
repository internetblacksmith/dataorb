import React, { useState, useEffect } from 'react';
import './App.css';

interface PostHogStats {
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
  metrics: {
    top: { type: string; label: string; enabled: boolean };
    left: { type: string; label: string; enabled: boolean };
    right: { type: string; label: string; enabled: boolean };
  };
}

const App: React.FC = () => {
  const [stats, setStats] = useState<PostHogStats | null>(null);
  const [displayConfig, setDisplayConfig] = useState<DisplayConfig | null>(
    null,
  );
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deviceIP, setDeviceIP] = useState<string>('[device-ip]');

  const fetchStats = async () => {
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
      // Check if we're in WiFi setup mode (network error on localhost)
      const isLocalDisplay = window.location.hostname === 'localhost' || 
                           window.location.hostname === '127.0.0.1';
      
      if (isLocalDisplay && err instanceof TypeError && err.message.includes('fetch')) {
        // Network error on local display likely means WiFi AP mode
        setError('wifi-setup-mode');
      } else {
        setError('Failed to fetch stats');
      }
      console.error('Error fetching stats:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDisplayConfig = async () => {
    try {
      const response = await fetch('/api/admin/config');
      const data = await response.json();
      setDisplayConfig({ metrics: data.display.metrics });
    } catch (err) {
      console.error('Error fetching display config:', err);
    }
  };

  useEffect(() => {
    fetchStats();
    fetchDisplayConfig();
    
    // Get device IP address for display
    fetch('/api/admin/config')
      .then(res => res.json())
      .then(data => {
        if (data.network?.ip_address) {
          setDeviceIP(data.network.ip_address);
        }
      })
      .catch(() => {
        // Try to get IP from window location if not localhost
        const hostname = window.location.hostname;
        if (hostname && hostname !== 'localhost' && hostname !== '127.0.0.1') {
          setDeviceIP(hostname);
        }
      });
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchStats, 30000);
    
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
      
      if (lastUpdate && lastCheck && parseInt(lastUpdate) > parseInt(lastCheck)) {
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
        <p>Loading PostHog Stats...</p>
      </div>
    );
  }

  if (error) {
    // Check if accessing from localhost (LCD display) or remote (PC)
    const isLocalDisplay = window.location.hostname === 'localhost' || 
                          window.location.hostname === '127.0.0.1';
    
    // Auto-redirect only if accessing from remote PC
    if (!isLocalDisplay) {
      if (error.includes('PostHog credentials not configured')) {
        window.location.href = '/config';
        return (
          <div className="app loading">
            <div className="loading-spinner"></div>
            <p>Redirecting to configuration...</p>
          </div>
        );
      }
      
      if (error.includes('401')) {
        window.location.href = '/config?error=401';
        return (
          <div className="app loading">
            <div className="loading-spinner"></div>
            <p>Authentication error - redirecting to configuration...</p>
          </div>
        );
      }
      
      if (error.includes('403')) {
        window.location.href = '/config?error=403';
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
            <div className="center-logo">
              <div className="logo-text">PostHog</div>
              <div className="logo-subtitle">WiFi Setup</div>
            </div>
            
            <div className="config-message" style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              padding: '20px',
              maxWidth: '85%'
            }}>
              <h2 style={{ color: '#1d4aff', marginBottom: '15px', fontSize: '24px' }}>Connect to WiFi</h2>
              
              <div style={{ 
                background: '#1e293b', 
                padding: '12px', 
                borderRadius: '10px',
                marginBottom: '15px',
                border: '2px solid #1d4aff'
              }}>
                <p style={{ fontSize: '14px', marginBottom: '8px', color: '#94a3b8' }}>
                  1. On your phone/laptop, connect to:
                </p>
                <div style={{ fontSize: '20px', fontWeight: 'bold', color: '#fff', marginBottom: '5px' }}>
                  📶 PostHog-Setup
                </div>
                <p style={{ fontSize: '12px', color: '#94a3b8' }}>
                  Password: <span style={{ fontFamily: 'monospace', color: '#10b981' }}>posthog123</span>
                </p>
              </div>
              
              <div style={{ 
                background: '#1e293b', 
                padding: '10px', 
                borderRadius: '10px',
                fontSize: '14px'
              }}>
                <p style={{ marginBottom: '5px', color: '#94a3b8' }}>
                  2. Visit in browser:
                </p>
                <div style={{ fontFamily: 'monospace', fontSize: '16px', color: '#10b981' }}>
                  192.168.4.1:5000
                </div>
              </div>
              
              <p style={{ fontSize: '11px', color: '#64748b', marginTop: '10px' }}>
                No network detected • Access Point mode active
              </p>
            </div>
            
            <div className="outer-ring"></div>
          </div>
        </div>
      );
    }
    
    // Show configuration message on LCD display
    if (error.includes('PostHog credentials not configured') || 
        error.includes('401') || 
        error.includes('403')) {
      return (
        <div className="app">
          <div className="circular-container">
            <div className="center-logo">
              <div className="logo-text">PostHog</div>
              <div className="logo-subtitle">Setup Required</div>
            </div>
            
            <div className="config-message" style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              padding: '20px',
              maxWidth: '80%'
            }}>
              <h2 style={{ color: '#1d4aff', marginBottom: '20px' }}>Configuration Needed</h2>
              <p style={{ fontSize: '18px', marginBottom: '15px' }}>
                Visit this device's IP address from your computer:
              </p>
              <div style={{ 
                background: '#1e293b', 
                padding: '15px', 
                borderRadius: '10px',
                fontSize: '20px',
                fontFamily: 'monospace',
                marginBottom: '15px'
              }}>
                http://{deviceIP}:5000/config
              </div>
              <p style={{ fontSize: '14px', color: '#94a3b8' }}>
                {error.includes('401') && 'Invalid API key'}
                {error.includes('403') && 'Permission error - check project access'}
                {error.includes('not configured') && 'PostHog credentials required'}
              </p>
            </div>
            
            <div className="outer-ring"></div>
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
          <div className="logo-text">PostHog</div>
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

import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useKeyboardNavigation, useTheme, useNetworkStatus } from '../../hooks';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { PostHogConfig } from './PostHogConfig';
import { DisplayConfig } from './DisplayConfig';
import { NetworkConfig } from './NetworkConfig';
import { ThemeConfig } from './ThemeConfig';
import { OTAConfig } from './OTAConfig';
import { DeviceConfig, Theme, OTAStatus, AvailableMetric } from '../../types';
import { API_ENDPOINTS } from '../../constants';
import './styles.css';
import '../../themes.css';

type TabType = 'posthog' | 'display' | 'network' | 'themes' | 'updates';

const ConfigPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  
  // State
  const [config, setConfig] = useState<DeviceConfig | null>(null);
  const [themes, setThemes] = useState<Theme[]>([]);
  const [otaStatus, setOtaStatus] = useState<OTAStatus | null>(null);
  const [availableMetrics, setAvailableMetrics] = useState<AvailableMetric[]>([]);
  const [activeTab, setActiveTab] = useState<TabType>('posthog');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Custom hooks
  useKeyboardNavigation();
  const { networkStatus } = useNetworkStatus();
  const { applyTheme } = useTheme(config?.display?.theme);

  // Initialize tab from URL on mount
  useEffect(() => {
    const tab = searchParams.get('tab');
    const validTabs: TabType[] = ['posthog', 'display', 'network', 'themes', 'updates'];
    
    if (tab && validTabs.includes(tab as TabType)) {
      setActiveTab(tab as TabType);
    } else {
      // Set default tab in URL if not present or invalid
      setSearchParams({ tab: 'posthog' }, { replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run on mount

  // Update URL when activeTab changes
  useEffect(() => {
    const currentTab = searchParams.get('tab');
    if (currentTab !== activeTab) {
      setSearchParams({ tab: activeTab }, { replace: false });
    }
  }, [activeTab, searchParams, setSearchParams])

  const loadConfig = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.CONFIG);
      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to load configuration' });
    }
  }, []);

  const loadThemes = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.THEMES);
      if (response.ok) {
        const data = await response.json();
        setThemes(data);
      }
    } catch {
      // Handle silently
    }
  }, []);

  const loadOTAStatus = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.OTA_STATUS);
      if (response.ok) {
        const data = await response.json();
        setOtaStatus(data);
      }
    } catch {
      // Handle silently
    }
  }, []);

  const loadAvailableMetrics = useCallback(async () => {
    try {
      const response = await fetch(API_ENDPOINTS.AVAILABLE_METRICS);
      if (response.ok) {
        const data = await response.json();
        // Transform the object format to array format
        const metricsArray = Object.entries(data).map(([id, metric]: [string, any]) => ({
          id,
          name: metric.label,
          description: metric.description,
          category: id.includes('user') ? 'users' : id.includes('session') ? 'sessions' : 'events',
        }));
        setAvailableMetrics(metricsArray);
      }
    } catch {
      // Use default metrics if API fails
      setAvailableMetrics([
        { id: 'events_24h', name: 'Events (24h)', description: 'Total events in last 24 hours', category: 'events' },
        { id: 'unique_users_24h', name: 'Users (24h)', description: 'Unique users in last 24 hours', category: 'users' },
        { id: 'page_views_24h', name: 'Page Views (24h)', description: 'Page view events in last 24 hours', category: 'events' },
        { id: 'custom_events_24h', name: 'Custom Events (24h)', description: 'Non-pageview events in last 24 hours', category: 'events' },
        { id: 'sessions_24h', name: 'Sessions (24h)', description: 'Unique sessions in last 24 hours', category: 'sessions' },
        { id: 'events_1h', name: 'Events (1h)', description: 'Events in last hour', category: 'events' },
        { id: 'avg_events_per_user', name: 'Avg Events/User', description: 'Average events per user', category: 'users' },
      ]);
    }
  }, []);

  // Load initial data
  useEffect(() => {
    Promise.all([
      loadConfig(),
      loadThemes(),
      loadOTAStatus(),
      loadAvailableMetrics(),
    ]).finally(() => setLoading(false));
  }, [loadConfig, loadThemes, loadOTAStatus, loadAvailableMetrics]);

  const handleConfigChange = useCallback((updates: Partial<DeviceConfig>) => {
    if (!config) return;
    
    const updatedConfig = {
      ...config,
      ...updates,
    };
    
    setConfig(updatedConfig);
  }, [config]);

  const saveConfig = useCallback(async () => {
    if (!config) return;
    
    setSaving(true);
    setMessage(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.CONFIG, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });
      
      if (response.ok) {
        setMessage({ type: 'success', text: 'Configuration saved successfully!' });
        
        // Broadcast config update
        const channel = new BroadcastChannel('config-updates');
        channel.postMessage({ type: 'displayConfigUpdated', config: config.display });
        channel.close();
        
        // Apply theme if changed
        if (config.display?.theme) {
          applyTheme(config.display.theme);
        }
      } else {
        throw new Error('Failed to save configuration');
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to save configuration' });
    } finally {
      setSaving(false);
    }
  }, [config, applyTheme]);

  const deleteTheme = useCallback(async (themeId: string) => {
    try {
      const response = await fetch(API_ENDPOINTS.THEME_BY_ID(themeId), {
        method: 'DELETE',
      });
      
      if (response.ok) {
        setThemes(prev => prev.filter(t => t.id !== themeId));
        
        // Reset to dark theme if deleted theme was active
        if (config?.display?.theme === themeId) {
          handleConfigChange({ display: { ...config.display, theme: 'dark' } });
        }
      }
    } catch {
      setMessage({ type: 'error', text: 'Failed to delete theme' });
    }
  }, [config, handleConfigChange]);

  const tabs: Array<{ id: TabType; label: string; icon: string }> = [
    { id: 'posthog', label: 'PostHog', icon: '📊' },
    { id: 'display', label: 'Display', icon: '🎨' },
    { id: 'network', label: 'Network', icon: '🌐' },
    { id: 'themes', label: 'Themes', icon: '🎭' },
    { id: 'updates', label: 'Updates', icon: '🔄' },
  ];

  if (loading) {
    return (
      <div className="config-page loading">
        <LoadingSpinner size="large" message="Loading configuration..." />
      </div>
    );
  }

  if (!config) {
    return (
      <div className="config-page error">
        <h2>Error Loading Configuration</h2>
        <button className="btn-primary" onClick={() => window.location.reload()}>
          Reload Page
        </button>
      </div>
    );
  }

  return (
    <div className="config-page">
      <div className="config-header">
        <h1>DataOrb Configuration</h1>
        <div className="header-actions">
          <button
            className="btn-primary"
            onClick={saveConfig}
            disabled={saving}
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
          <button
            className="btn-secondary"
            onClick={() => navigate('/')}
          >
            Back to Dashboard
          </button>
        </div>
      </div>

      {message && (
        <div className={`message ${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="config-content">
        <div className="config-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="config-panel">
          {activeTab === 'posthog' && (
            <PostHogConfig config={config} onChange={handleConfigChange} />
          )}
          
          {activeTab === 'display' && (
            <DisplayConfig 
              config={config} 
              availableMetrics={availableMetrics}
              onChange={handleConfigChange} 
            />
          )}
          
          {activeTab === 'network' && (
            <NetworkConfig 
              config={config} 
              networkStatus={networkStatus}
              onChange={handleConfigChange} 
            />
          )}
          
          {activeTab === 'themes' && (
            <ThemeConfig 
              config={config} 
              themes={themes}
              onChange={handleConfigChange}
              onDeleteTheme={deleteTheme}
            />
          )}
          
          {activeTab === 'updates' && (
            <OTAConfig 
              config={config} 
              otaStatus={otaStatus}
              onChange={handleConfigChange}
              onRefreshStatus={loadOTAStatus}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default ConfigPage;
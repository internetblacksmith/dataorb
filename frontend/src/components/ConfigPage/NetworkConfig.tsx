import React, { useState } from 'react';
import { DeviceConfig, NetworkStatus } from '../../types';
import { API_ENDPOINTS } from '../../constants';

interface NetworkConfigProps {
  config: DeviceConfig;
  networkStatus: NetworkStatus | null;
  onChange: (updates: Partial<DeviceConfig>) => void;
}

export const NetworkConfig: React.FC<NetworkConfigProps> = React.memo(({ 
  config, 
  networkStatus,
  onChange 
}) => {
  const [availableNetworks, setAvailableNetworks] = useState<string[]>([]);
  const [scanning, setScanning] = useState(false);
  const [connecting, setConnecting] = useState(false);

  const handleWiFiChange = (field: 'ssid' | 'password', value: string) => {
    onChange({
      wifi: {
        ...config.wifi,
        [field]: value,
      },
    });
  };

  const scanNetworks = async () => {
    setScanning(true);
    try {
      const response = await fetch(API_ENDPOINTS.NETWORK_SCAN);
      if (response.ok) {
        const data = await response.json();
        setAvailableNetworks(data.networks || []);
      }
    } catch {
      // Handle error silently
    } finally {
      setScanning(false);
    }
  };

  const connectToNetwork = async () => {
    if (!config.wifi?.ssid || !config.wifi?.password) return;
    
    setConnecting(true);
    try {
      const response = await fetch(API_ENDPOINTS.NETWORK_CONNECT, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ssid: config.wifi.ssid,
          password: config.wifi.password,
        }),
      });
      
      if (response.ok) {
        // Network connection initiated
        setTimeout(() => window.location.reload(), 5000);
      }
    } catch {
      // Handle error silently
    } finally {
      setConnecting(false);
    }
  };

  return (
    <div className="config-section">
      <h2>Network Configuration</h2>

      {/* Current Network Status */}
      <div className="info-grid">
        <div className="info-card">
          <h3>Current Network Status</h3>
          <p>
            <strong>Status:</strong>{' '}
            {networkStatus?.connected ? (
              <span style={{ color: '#10b981' }}>Connected</span>
            ) : (
              <span style={{ color: '#ef4444' }}>Disconnected</span>
            )}
          </p>
          {networkStatus?.ssid && (
            <p>
              <strong>Network:</strong> {networkStatus.ssid}
            </p>
          )}
          {networkStatus?.ip && (
            <p>
              <strong>IP Address:</strong> {networkStatus.ip}
            </p>
          )}
          {networkStatus?.signal_strength !== undefined && (
            <p>
              <strong>Signal:</strong> {networkStatus.signal_strength}%
            </p>
          )}
          {networkStatus?.ap_mode && (
            <p style={{ color: '#fbbf24' }}>
              <strong>Access Point Mode Active</strong>
              <br />
              SSID: {networkStatus.ap_ssid || 'DataOrb-Setup'}
              <br />
              IP: {networkStatus.ap_ip || '192.168.4.1'}
            </p>
          )}
        </div>
      </div>

      {/* WiFi Configuration */}
      <h3>WiFi Settings</h3>
      
      <div className="form-group">
        <label htmlFor="wifi-ssid">Network Name (SSID)</label>
        <div style={{ display: 'flex', gap: '10px' }}>
          <input
            id="wifi-ssid"
            type="text"
            value={config.wifi?.ssid || ''}
            onChange={(e) => handleWiFiChange('ssid', e.target.value)}
            placeholder="Your WiFi network name"
            style={{ flex: 1 }}
          />
          <button
            className="btn-secondary"
            onClick={scanNetworks}
            disabled={scanning}
          >
            {scanning ? 'Scanning...' : 'Scan'}
          </button>
        </div>
      </div>

      {availableNetworks.length > 0 && (
        <div className="form-group">
          <label>Available Networks</label>
          <select
            value={config.wifi?.ssid || ''}
            onChange={(e) => handleWiFiChange('ssid', e.target.value)}
          >
            <option value="">Select a network...</option>
            {availableNetworks.map((network) => (
              <option key={network} value={network}>
                {network}
              </option>
            ))}
          </select>
        </div>
      )}

      <div className="form-group">
        <label htmlFor="wifi-password">Password</label>
        <input
          id="wifi-password"
          type="password"
          value={config.wifi?.password || ''}
          onChange={(e) => handleWiFiChange('password', e.target.value)}
          placeholder="WiFi password"
        />
      </div>

      <button
        className="btn-primary"
        onClick={connectToNetwork}
        disabled={!config.wifi?.ssid || !config.wifi?.password || connecting}
      >
        {connecting ? 'Connecting...' : 'Connect to Network'}
      </button>

      {/* Device Information */}
      <h3 style={{ marginTop: '30px' }}>Device Information</h3>
      
      <div className="form-group">
        <label htmlFor="device-name">Device Name</label>
        <input
          id="device-name"
          type="text"
          value={config.device_name || ''}
          onChange={(e) => onChange({ device_name: e.target.value })}
          placeholder="My DataOrb"
        />
      </div>

      <div className="form-group">
        <label htmlFor="location">Location</label>
        <input
          id="location"
          type="text"
          value={config.location || ''}
          onChange={(e) => onChange({ location: e.target.value })}
          placeholder="Office, Living Room, etc."
        />
      </div>

      <div className="form-group">
        <label>Device ID</label>
        <input
          type="text"
          value={config.device_id || 'Unknown'}
          disabled
          style={{ opacity: 0.6 }}
        />
      </div>
    </div>
  );
});

NetworkConfig.displayName = 'NetworkConfig';
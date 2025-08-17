import React, { useState } from 'react';
import { DeviceConfig, OTAStatus } from '../../types';
import { API_ENDPOINTS } from '../../constants';

interface OTAConfigProps {
  config: DeviceConfig;
  otaStatus: OTAStatus | null;
  onChange: (updates: Partial<DeviceConfig>) => void;
  onRefreshStatus: () => void;
}

export const OTAConfig: React.FC<OTAConfigProps> = React.memo(({ 
  config, 
  otaStatus,
  onChange,
  onRefreshStatus
}) => {
  const [checking, setChecking] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [switchingBranch, setSwitchingBranch] = useState(false);

  const handleOTAChange = (field: keyof NonNullable<DeviceConfig['ota']>, value: any) => {
    onChange({
      ota: {
        ...config.ota,
        [field]: value,
      } as DeviceConfig['ota'],
    });
  };

  const checkForUpdates = async () => {
    setChecking(true);
    try {
      const response = await fetch(API_ENDPOINTS.OTA_CHECK);
      if (response.ok) {
        onRefreshStatus();
      }
    } catch {
      // Handle error silently
    } finally {
      setChecking(false);
    }
  };

  const applyUpdate = async () => {
    if (!otaStatus?.update_available) return;
    
    setUpdating(true);
    try {
      const response = await fetch(API_ENDPOINTS.OTA_UPDATE, {
        method: 'POST',
      });
      
      if (response.ok) {
        // Update initiated, will restart
        setTimeout(() => window.location.reload(), 10000);
      }
    } catch {
      // Handle error silently
    } finally {
      setUpdating(false);
    }
  };

  const switchBranch = async (branch: string) => {
    setSwitchingBranch(true);
    try {
      const response = await fetch(API_ENDPOINTS.OTA_SWITCH_BRANCH, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ branch }),
      });
      
      if (response.ok) {
        handleOTAChange('branch', branch);
        onRefreshStatus();
      }
    } catch {
      // Handle error silently
    } finally {
      setSwitchingBranch(false);
    }
  };

  return (
    <div className="config-section">
      <h2>Over-the-Air Updates</h2>

      {/* OTA Status */}
      <div className="info-grid">
        <div className="info-card">
          <h3>Update Status</h3>
          <p>
            <strong>Updates:</strong>{' '}
            {otaStatus?.enabled ? (
              <span style={{ color: '#10b981' }}>Enabled</span>
            ) : (
              <span style={{ color: '#ef4444' }}>Disabled</span>
            )}
          </p>
          <p>
            <strong>Current Branch:</strong> {otaStatus?.branch || 'main'}
          </p>
          <p>
            <strong>Current Version:</strong> {otaStatus?.current_version || 'Unknown'}
          </p>
          {otaStatus?.update_available && (
            <p style={{ color: '#fbbf24' }}>
              <strong>Update Available!</strong>
              <br />
              Latest: {otaStatus.latest_version}
            </p>
          )}
          {otaStatus?.last_check && (
            <p>
              <strong>Last Check:</strong>{' '}
              {new Date(otaStatus.last_check).toLocaleString()}
            </p>
          )}
          {otaStatus?.error && (
            <p style={{ color: '#ef4444' }}>
              <strong>Error:</strong> {otaStatus.error}
            </p>
          )}
        </div>
      </div>

      {/* OTA Settings */}
      <h3>Update Settings</h3>
      
      <div className="form-group">
        <label>
          <input
            type="checkbox"
            checked={config.ota?.enabled ?? false}
            onChange={(e) => handleOTAChange('enabled', e.target.checked)}
          />
          Enable automatic update checks
        </label>
      </div>

      <div className="form-group">
        <label>
          <input
            type="checkbox"
            checked={config.ota?.check_on_boot ?? false}
            onChange={(e) => handleOTAChange('check_on_boot', e.target.checked)}
            disabled={!config.ota?.enabled}
          />
          Check for updates on boot
        </label>
      </div>

      <div className="form-group">
        <label>
          <input
            type="checkbox"
            checked={config.ota?.auto_pull ?? false}
            onChange={(e) => handleOTAChange('auto_pull', e.target.checked)}
            disabled={!config.ota?.enabled}
          />
          Automatically apply updates
        </label>
      </div>

      {/* Branch Selection */}
      <div className="form-group">
        <label>Update Branch</label>
        <select
          value={config.ota?.branch || 'main'}
          onChange={(e) => switchBranch(e.target.value)}
          disabled={switchingBranch}
        >
          <option value="main">Main (Stable)</option>
          <option value="dev">Development (Latest Features)</option>
          <option value="canary">Canary (Experimental)</option>
        </select>
        {switchingBranch && <span> Switching branch...</span>}
      </div>

      {/* Action Buttons */}
      <div className="theme-actions">
        <button
          className="btn-primary"
          onClick={checkForUpdates}
          disabled={checking || updating}
        >
          {checking ? 'Checking...' : 'Check for Updates'}
        </button>

        {otaStatus?.update_available && (
          <button
            className="btn-secondary"
            onClick={applyUpdate}
            disabled={updating}
          >
            {updating ? 'Updating...' : 'Apply Update Now'}
          </button>
        )}

        <button
          className="btn-secondary"
          onClick={onRefreshStatus}
          disabled={checking || updating}
        >
          Refresh Status
        </button>
      </div>

      {/* Branch Information */}
      <div className="info-card" style={{ marginTop: '20px' }}>
        <h3>Branch Information</h3>
        <ul>
          <li>
            <strong>Main:</strong> Stable releases, thoroughly tested
          </li>
          <li>
            <strong>Dev:</strong> Latest features, may have minor issues
          </li>
          <li>
            <strong>Canary:</strong> Experimental features, use with caution
          </li>
        </ul>
      </div>
    </div>
  );
});

OTAConfig.displayName = 'OTAConfig';
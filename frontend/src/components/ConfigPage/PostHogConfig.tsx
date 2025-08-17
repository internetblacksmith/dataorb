import React from 'react';
import { DeviceConfig } from '../../types';

interface PostHogConfigProps {
  config: DeviceConfig;
  onChange: (updates: Partial<DeviceConfig>) => void;
}

export const PostHogConfig: React.FC<PostHogConfigProps> = React.memo(({ config, onChange }) => {
  const handlePostHogChange = (field: keyof NonNullable<DeviceConfig['posthog']>, value: string) => {
    onChange({
      posthog: {
        ...config.posthog,
        [field]: value,
      },
    });
  };

  return (
    <div className="config-section">
      <h2>PostHog Configuration</h2>
      
      <div className="form-group">
        <label htmlFor="api-key">API Key</label>
        <input
          id="api-key"
          type="password"
          value={config.posthog?.api_key || ''}
          onChange={(e) => handlePostHogChange('api_key', e.target.value)}
          placeholder="phc_..."
        />
      </div>

      <div className="form-group">
        <label htmlFor="host">Host URL</label>
        <input
          id="host"
          type="url"
          value={config.posthog?.host || 'https://app.posthog.com'}
          onChange={(e) => handlePostHogChange('host', e.target.value)}
          placeholder="https://app.posthog.com"
        />
      </div>

      <div className="form-group">
        <label htmlFor="project-id">Project ID</label>
        <input
          id="project-id"
          type="text"
          value={config.posthog?.project_id || ''}
          onChange={(e) => handlePostHogChange('project_id', e.target.value)}
          placeholder="Optional"
        />
      </div>

      <div className="info-card">
        <h3>Getting Your API Key</h3>
        <ol>
          <li>Log in to your PostHog account</li>
          <li>Go to Project Settings → API Keys</li>
          <li>Copy your Personal API Key</li>
          <li>Paste it above and save</li>
        </ol>
      </div>
    </div>
  );
});

PostHogConfig.displayName = 'PostHogConfig';
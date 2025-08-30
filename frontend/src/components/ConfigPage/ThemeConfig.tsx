import React from 'react';
import { DeviceConfig, Theme } from '../../types';

interface ThemeConfigProps {
  config: DeviceConfig;
  themes: Theme[];
  onChange: (updates: Partial<DeviceConfig>) => void;
  onDeleteTheme: (themeId: string) => void;
}

export const ThemeConfig: React.FC<ThemeConfigProps> = React.memo(({ 
  config, 
  themes,
  onChange,
  onDeleteTheme
}) => {
  const handleThemeSelect = (themeId: string) => {
    onChange({
      display: {
        ...config.display,
        theme: themeId,
      },
    });
  };

  // Separate built-in and custom themes
  const builtInThemes = themes.filter(t => !t.isCustom && !t.custom);
  const customThemes = themes.filter(t => t.isCustom || t.custom);

  return (
    <div className="config-section">
      <h2>Theme Settings</h2>

      <div className="form-group">
        <label>Built-in Themes</label>
        <div className="theme-grid">
          {builtInThemes.map((theme) => (
            <div
              key={theme.id}
              className={`theme-card ${config.display?.theme === theme.id ? 'active' : ''}`}
            >
              <h5>{theme.name}</h5>
              <p>{theme.description || 'Built-in theme'}</p>
              <div className="theme-card-actions">
                <button
                  className={config.display?.theme === theme.id ? 'selected' : 'select'}
                  onClick={() => handleThemeSelect(theme.id)}
                  disabled={config.display?.theme === theme.id}
                >
                  {config.display?.theme === theme.id ? '✓ Selected' : 'Select'}
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Custom Themes Section */}
      {customThemes.length > 0 && (
        <div className="form-group">
          <label>Custom Themes</label>
          <div className="theme-grid">
            {customThemes.map((theme) => (
              <div
                key={theme.id}
                className={`theme-card ${config.display?.theme === theme.id ? 'active' : ''}`}
              >
                <h5>
                  {theme.name}
                  <span className="custom-badge">Custom</span>
                </h5>
                <p>{theme.description || 'Custom theme with brand colors'}</p>
                <div className="theme-card-actions">
                  <button
                    className={config.display?.theme === theme.id ? 'selected' : 'select'}
                    onClick={() => handleThemeSelect(theme.id)}
                    disabled={config.display?.theme === theme.id}
                  >
                    {config.display?.theme === theme.id ? '✓ Selected' : 'Select'}
                  </button>
                  <button
                    className="delete"
                    onClick={() => onDeleteTheme(theme.id)}
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Theme Preview */}
      <div className="info-card">
        <h3>Theme Information</h3>
        <p>
          Themes control the overall appearance of your dashboard including colors, 
          backgrounds, and branding elements.
        </p>
        <ul>
          <li><strong>Dark Mode:</strong> Best for low-light environments</li>
          <li><strong>Light Mode:</strong> Better visibility in bright conditions</li>
          <li><strong>Custom Themes:</strong> Include company branding and logos</li>
        </ul>
      </div>

    </div>
  );
});

ThemeConfig.displayName = 'ThemeConfig';
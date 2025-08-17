import React from 'react';
import './styles.css';

interface ErrorDisplayProps {
  error: string;
  onRetry?: () => void;
  showRetry?: boolean;
}

export const ErrorDisplay: React.FC<ErrorDisplayProps> = React.memo(({
  error,
  onRetry,
  showRetry = true,
}) => {
  const isWifiSetup = error === 'wifi-setup-mode';

  if (isWifiSetup) {
    return (
      <div className="error-display wifi-setup">
        <div className="error-icon">📡</div>
        <h2>WiFi Setup Mode</h2>
        <div className="setup-steps">
          <div className="setup-step">
            <div className="step-number">1</div>
            <div>
              <p>Connect to WiFi network:</p>
              <strong>DataOrb-Setup</strong>
            </div>
          </div>
          <div className="setup-step">
            <div className="step-number">2</div>
            <div>
              <p>Open browser and go to:</p>
              <strong>192.168.4.1</strong>
            </div>
          </div>
          <div className="setup-step">
            <div className="step-number">3</div>
            <div>
              <p>Follow setup wizard</p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="error-display">
      <div className="error-icon">⚠️</div>
      <h2>Error</h2>
      <p className="error-message">{error}</p>
      {showRetry && onRetry && (
        <button className="retry-button" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
});

ErrorDisplay.displayName = 'ErrorDisplay';
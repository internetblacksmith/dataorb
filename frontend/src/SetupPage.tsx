import React, { useState, useEffect } from 'react';
import './SetupPage.css';

interface NetworkStatus {
  wifi_status: {
    status: string;
    ssid: string;
    signal: string;
  };
  network_connected: boolean;
  ap_active: boolean;
}

interface WiFiNetwork {
  ssid: string;
  quality: string;
  encryption: string;
}

const SetupPage: React.FC = () => {
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus | null>(
    null,
  );
  const [availableNetworks, setAvailableNetworks] = useState<WiFiNetwork[]>([]);
  const [selectedNetwork, setSelectedNetwork] = useState<string>('');
  const [wifiPassword, setWifiPassword] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string>('');
  const [step, setStep] = useState<
    'welcome' | 'networks' | 'connecting' | 'success'
  >('welcome');

  const API_BASE = process.env.REACT_APP_API_URL || '';

  useEffect(() => {
    fetchNetworkStatus();
  }, []);

  const fetchNetworkStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/network/status`);
      const data = await response.json();
      setNetworkStatus(data);

      if (data.network_connected) {
        setStep('success');
      }
    } catch (error) {
      console.error('Error fetching network status:', error);
    }
  };

  const scanNetworks = async () => {
    setLoading(true);
    setMessage('Scanning for WiFi networks...');

    try {
      const response = await fetch(`${API_BASE}/api/network/scan`);
      const networks = await response.json();
      setAvailableNetworks(networks);
      setStep('networks');
      setMessage('');
    } catch (error) {
      setMessage('Failed to scan networks. Please try again.');
      console.error('Error scanning networks:', error);
    } finally {
      setLoading(false);
    }
  };

  const connectToNetwork = async () => {
    if (!selectedNetwork || !wifiPassword) {
      setMessage('Please select a network and enter password');
      return;
    }

    setLoading(true);
    setStep('connecting');
    setMessage('Connecting to WiFi network...');

    try {
      // First save the network config
      const configResponse = await fetch(`${API_BASE}/api/admin/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          network: {
            wifi_ssid: selectedNetwork,
            wifi_password: wifiPassword,
            use_dhcp: true,
          },
        }),
      });

      if (!configResponse.ok) {
        throw new Error('Failed to save network configuration');
      }

      // Then attempt to connect
      const connectResponse = await fetch(`${API_BASE}/api/network/connect`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ssid: selectedNetwork,
          password: wifiPassword,
        }),
      });

      const result = await connectResponse.json();

      if (result.success) {
        setMessage('Connected successfully! Switching to normal mode...');
        setStep('success');

        // Wait a moment then reload to switch to normal dashboard
        setTimeout(() => {
          window.location.href = '/';
        }, 3000);
      } else {
        setMessage(
          'Failed to connect. Please check your password and try again.',
        );
        setStep('networks');
      }
    } catch (error) {
      setMessage('Connection failed. Please try again.');
      setStep('networks');
      console.error('Error connecting to network:', error);
    } finally {
      setLoading(false);
    }
  };

  const renderWelcome = () => (
    <div className="setup-content">
      <div className="setup-header">
        <div className="setup-logo">
          <div className="logo-circle">
            <div className="logo-text">DataOrb</div>
            <div className="logo-subtitle">Setup</div>
          </div>
        </div>
        <h1>Welcome to DataOrb</h1>
        <p>Let's connect your analytics dashboard to the internet</p>
      </div>

      <div className="setup-status">
        {networkStatus?.network_connected ? (
          <div className="status-card connected">
            <div className="status-icon">✅</div>
            <div className="status-info">
              <h3>Network Connected</h3>
              <p>
                Connected to: <strong>{networkStatus.wifi_status.ssid}</strong>
              </p>
              <p>Your DataOrb is online and ready!</p>
            </div>
          </div>
        ) : (
          <div className="status-card disconnected">
            <div className="status-icon">🔌</div>
            <div className="status-info">
              <h3>No Internet Connection</h3>
              <p>Click below to connect to your WiFi network</p>
            </div>
          </div>
        )}
      </div>

      <div className="setup-actions">
        <button
          onClick={scanNetworks}
          disabled={loading}
          className="setup-button primary"
        >
          {loading ? 'Scanning...' : 'Connect to WiFi Network'}
        </button>

        <button
          onClick={() => (window.location.href = '/config')}
          className="setup-button secondary"
        >
          Configure DataOrb Settings
        </button>
      </div>

      {networkStatus?.network_connected && (
        <div className="setup-instructions">
          <h3>Next Steps</h3>
          <ol>
            <li>Click "Configure DataOrb Settings" above</li>
            <li>Enter your PostHog API credentials</li>
            <li>Customize your dashboard display</li>
            <li>Start viewing your analytics!</li>
          </ol>
        </div>
      )}
    </div>
  );

  const renderNetworks = () => (
    <div className="setup-content">
      <div className="setup-header">
        <h1>Choose WiFi Network</h1>
        <p>Select a network and enter the password</p>
      </div>

      <div className="networks-list">
        {availableNetworks.map((network, index) => (
          <div
            key={index}
            className={`network-item ${selectedNetwork === network.ssid ? 'selected' : ''}`}
            onClick={() => setSelectedNetwork(network.ssid)}
          >
            <div className="network-info">
              <div className="network-name">{network.ssid}</div>
              <div className="network-details">
                <span className="network-quality">{network.quality}</span>
                <span className="network-security">
                  {network.encryption === 'on' ? '🔒' : '🔓'}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {selectedNetwork && (
        <div className="password-section">
          <label htmlFor="wifi-password">Password for {selectedNetwork}:</label>
          <input
            id="wifi-password"
            type="password"
            value={wifiPassword}
            onChange={(e) => setWifiPassword(e.target.value)}
            placeholder="Enter WiFi password"
            className="password-input"
          />
        </div>
      )}

      <div className="setup-actions">
        <button
          onClick={connectToNetwork}
          disabled={loading || !selectedNetwork || !wifiPassword}
          className="setup-button primary"
        >
          Connect to Network
        </button>

        <button
          onClick={() => setStep('welcome')}
          className="setup-button secondary"
        >
          Back
        </button>
      </div>
    </div>
  );

  const renderConnecting = () => (
    <div className="setup-content">
      <div className="setup-header">
        <h1>Connecting...</h1>
        <p>Connecting to {selectedNetwork}</p>
      </div>

      <div className="connecting-animation">
        <div className="spinner"></div>
        <p>This may take a few moments...</p>
      </div>
    </div>
  );

  const renderSuccess = () => (
    <div className="setup-content">
      <div className="setup-header">
        <div className="success-icon">✅</div>
        <h1>Setup Complete!</h1>
        <p>Your DataOrb is now connected to the internet</p>
      </div>

      <div className="success-info">
        <p>
          You can now configure your PostHog settings and start viewing
          analytics.
        </p>
        <p>Redirecting to dashboard...</p>
      </div>
    </div>
  );

  return (
    <div className="setup-page">
      <div className="setup-container">
        {step === 'welcome' && renderWelcome()}
        {step === 'networks' && renderNetworks()}
        {step === 'connecting' && renderConnecting()}
        {step === 'success' && renderSuccess()}

        {message && (
          <div
            className={`setup-message ${message.includes('Failed') || message.includes('Error') ? 'error' : ''}`}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
};

export default SetupPage;

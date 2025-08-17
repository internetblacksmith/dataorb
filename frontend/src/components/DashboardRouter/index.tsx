import React, { useEffect, useState } from 'react';
import DashboardClassic from '../DashboardClassic';
import DashboardModern from '../DashboardModern';
import DashboardAnalytics from '../DashboardAnalytics';
import DashboardExecutive from '../DashboardExecutive';

interface DisplayConfig {
  layout?: string;
  theme?: string;
}

const DashboardRouter: React.FC = () => {
  const [layout, setLayout] = useState<string>('executive');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch the config to determine which layout to show
    const fetchConfig = async () => {
      try {
        const response = await fetch('/api/admin/config');
        if (response.ok) {
          const data = await response.json();
          const displayConfig = data.display as DisplayConfig;
          if (displayConfig?.layout) {
            setLayout(displayConfig.layout);
          }
        }
      } catch (error) {
        // Failed to fetch config, using default layout
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();

    // Listen for config changes via BroadcastChannel
    const channel = new BroadcastChannel('config-updates');
    channel.onmessage = (event) => {
      if (event.data.type === 'config-update' && event.data.config?.display?.layout) {
        setLayout(event.data.config.display.layout);
      }
    };

    return () => {
      channel.close();
    };
  }, []);

  if (loading) {
    return (
      <div style={{
        width: '100vw',
        height: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: '#0a0f1b',
        color: '#ffffff'
      }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{
            width: '60px',
            height: '60px',
            border: '3px solid rgba(244, 76, 4, 0.3)',
            borderTopColor: '#f44c04',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 20px'
          }} />
          <style dangerouslySetInnerHTML={{ __html: `
            @keyframes spin {
              from { transform: rotate(0deg); }
              to { transform: rotate(360deg); }
            }
          `}} />
          <div>Loading Dashboard...</div>
        </div>
      </div>
    );
  }

  // Return the appropriate dashboard based on the layout setting
  switch (layout) {
    case 'classic':
      return <DashboardClassic />;
    case 'modern':
      return <DashboardModern />;
    case 'analytics':
      return <DashboardAnalytics />;
    case 'executive':
    default:
      return <DashboardExecutive />;
  }
};

export default DashboardRouter;
import React, { useEffect, useState } from 'react';
import { DisplayConfig } from '../../types';
import DashboardClassic from '../DashboardClassic';
import DashboardModern from '../DashboardModern';
import DashboardAnalytics from '../DashboardAnalytics';
import DashboardExecutive from '../DashboardExecutive';

const DashboardRouter: React.FC = () => {
  const [layout, setLayout] = useState<string>('executive');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
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
      } catch {
        // Failed to fetch config, using default layout
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();

    if ('BroadcastChannel' in window) {
      const channel = new BroadcastChannel('config-updates');
      channel.onmessage = (event) => {
        if (event.data.type === 'config-update' && event.data.config?.display?.layout) {
          setLayout(event.data.config.display.layout);
        }
      };
      return () => channel.close();
    }
  }, []);

  if (loading) {
    return (
      <div className="router-loading">
        <div className="router-loading-inner">
          <div className="router-spinner" />
          <div>Loading Dashboard...</div>
        </div>
      </div>
    );
  }

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

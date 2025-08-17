// Shared TypeScript types and interfaces

// New metric object structure
export interface MetricObject {
  label: string;
  value: number;
}

// Dashboard-specific response types
export interface ClassicDashboardStats {
  top?: MetricObject;
  left?: MetricObject;
  right?: MetricObject;
  demo_mode: boolean;
  device_ip: string;
}

export interface ModernDashboardStats {
  primary?: MetricObject;
  secondaryLeft?: MetricObject;
  secondaryRight?: MetricObject;
  miniStat1?: MetricObject;
  miniStat2?: MetricObject;
  miniStat3?: MetricObject;
  demo_mode: boolean;
  device_ip: string;
  lastUpdated: string;
}

export interface AnalyticsDashboardStats {
  center?: MetricObject;
  top?: MetricObject;
  left?: MetricObject;
  right?: MetricObject;
  bottom?: MetricObject;
  stat1?: MetricObject;
  stat2?: MetricObject;
  stat3?: MetricObject;
  demo_mode: boolean;
  device_ip: string;
  lastUpdated: string;
}

export interface ExecutiveDashboardStats {
  north?: MetricObject;
  east?: MetricObject;
  south?: MetricObject;
  west?: MetricObject;
  northEast?: MetricObject;
  southEast?: MetricObject;
  southWest?: MetricObject;
  northWest?: MetricObject;
  demo_mode: boolean;
  device_ip: string;
  lastUpdated: string;
  recent_events?: Array<{
    event: string;
    user?: string;
    timestamp: string;
    properties?: Record<string, any>;
  }>;
}

// Legacy DataOrbStats interface (for backward compatibility)
export interface DataOrbStats {
  events_24h: number;
  unique_users_24h: number;
  page_views_24h: number;
  custom_events_24h: number;
  sessions_24h: number;
  events_1h: number;
  avg_events_per_user: number;
  recent_events: RecentEvent[];
  last_updated: string;
  error?: string;
  demo_mode?: boolean;
}

export interface RecentEvent {
  event: string;
  timestamp: string;
  properties?: Record<string, any>;
}

export interface DisplayConfig {
  theme?: string;
  layout?: string;
  refresh_interval?: number;
  metrics?: {
    classic?: {
      top?: MetricConfig;
      left?: MetricConfig;
      right?: MetricConfig;
    };
    modern?: {
      top?: MetricConfig;
      left?: MetricConfig;
      right?: MetricConfig;
      mini1?: MetricConfig;
      mini2?: MetricConfig;
      mini3?: MetricConfig;
    };
    analytics?: {
      top?: MetricConfig;
      left?: MetricConfig;
      right?: MetricConfig;
      bottom?: MetricConfig;
    };
    executive?: {
      north?: MetricConfig;
      east?: MetricConfig;
      south?: MetricConfig;
      west?: MetricConfig;
    };
  };
}

export interface MetricConfig {
  type: string;
  label: string;
  enabled: boolean;
}

export interface DeviceConfig {
  device_id: string;
  device_name?: string;
  location?: string;
  wifi?: {
    ssid?: string;
    password?: string;
  };
  posthog?: {
    api_key?: string;
    host?: string;
    project_id?: string;
  };
  display?: DisplayConfig;
  ota?: {
    enabled: boolean;
    branch: string;
    check_on_boot: boolean;
    auto_pull: boolean;
    last_update?: string;
  };
}

export interface NetworkStatus {
  connected: boolean;
  ssid?: string;
  ip?: string;
  signal_strength?: number;
  ap_mode: boolean;
  ap_ip?: string;
  ap_ssid?: string;
}

export interface Theme {
  id: string;
  name: string;
  description?: string;
  colors?: {
    background: string;
    containerBg: string;
    textColor: string;
    textSecondary: string;
    accent: string;
    accentSecondary: string;
    border: string;
    shadow: string;
    statBg: string;
    statBorder: string;
    statValue: string;
    statLabel: string;
    glowPrimary: string;
    glowSecondary: string;
    statusDot: string;
  };
  logo?: string;
  custom?: boolean;
  isCustom?: boolean;
}

export interface OTAStatus {
  enabled: boolean;
  branch: string;
  current_version?: string;
  latest_version?: string;
  update_available: boolean;
  last_check?: string;
  last_update?: string;
  updating?: boolean;
  error?: string;
}

export interface AvailableMetric {
  id: string;
  name: string;
  description: string;
  category: string;
  unit?: string;
}

// Utility types
export type MetricPosition = 'top' | 'left' | 'right' | 'north' | 'south' | 'east' | 'west';
export type DashboardLayout = 'classic' | 'modern' | 'analytics' | 'executive';
export type ThemeMode = 'dark' | 'light' | string;
// Application constants

export const API_ENDPOINTS = {
  STATS: '/api/stats',
  STATS_CLASSIC: '/api/stats/classic',
  STATS_MODERN: '/api/stats/modern',
  STATS_ANALYTICS: '/api/stats/analytics',
  STATS_EXECUTIVE: '/api/stats/executive',
  CONFIG: '/api/admin/config',
  DISPLAY_CONFIG: '/api/admin/config',
  NETWORK_STATUS: '/api/network/status',
  AVAILABLE_METRICS: '/api/metrics/available',
  THEMES: '/api/themes',
  THEME_BY_ID: (id: string) => `/api/themes/${id}`,
  OTA_STATUS: '/api/admin/ota/status',
  OTA_CHECK: '/api/admin/ota/check',
  OTA_UPDATE: '/api/admin/ota/update',
  OTA_SWITCH_BRANCH: '/api/admin/ota/switch-branch',
  NETWORK_SCAN: '/api/network/scan',
  NETWORK_CONNECT: '/api/network/connect',
} as const;

export const DASHBOARD_LAYOUTS = {
  CLASSIC: 'classic',
  MODERN: 'modern',
  ANALYTICS: 'analytics',
  EXECUTIVE: 'executive',
} as const;

export const KEYBOARD_SHORTCUTS = {
  DASHBOARD_CLASSIC: { ctrl: true, alt: true, key: '1' },
  DASHBOARD_MODERN: { ctrl: true, alt: true, key: '2' },
  DASHBOARD_ANALYTICS: { ctrl: true, alt: true, key: '3' },
  DASHBOARD_EXECUTIVE: { ctrl: true, alt: true, key: '4' },
  CONFIG: { ctrl: true, alt: true, key: '5' },
  CONFIG_ALTERNATE: { ctrl: true, shift: true, key: 'C' },
} as const;

export const REFRESH_INTERVALS = {
  STATS: 60000, // 60 seconds (1 minute)
  TIME: 1000, // 1 second
  OTA_CHECK: 300000, // 5 minutes
} as const;

export const METRIC_TYPES = {
  EVENTS_24H: 'events_24h',
  USERS_24H: 'unique_users_24h',
  PAGE_VIEWS_24H: 'page_views_24h',
  CUSTOM_EVENTS_24H: 'custom_events_24h',
  SESSIONS_24H: 'sessions_24h',
  EVENTS_1H: 'events_1h',
  AVG_EVENTS_PER_USER: 'avg_events_per_user',
} as const;

export const THEME_DEFAULTS = {
  DARK: 'dark',
  LIGHT: 'light',
} as const;

export const DISPLAY_DIMENSIONS = {
  WIDTH: 480,
  HEIGHT: 480,
  INNER_WIDTH: 460,
  INNER_HEIGHT: 460,
} as const;

export const CSS_VARIABLES = {
  BG_GRADIENT: '--bg-gradient',
  CONTAINER_BG: '--container-bg',
  TEXT_COLOR: '--text-color',
  TEXT_SECONDARY: '--text-secondary',
  ACCENT: '--accent',
  ACCENT_SECONDARY: '--accent-secondary',
  BORDER: '--border',
  SHADOW: '--shadow',
  STAT_BG: '--stat-bg',
  STAT_BORDER: '--stat-border',
  STAT_VALUE: '--stat-value',
  STAT_LABEL: '--stat-label',
  GLOW_PRIMARY: '--glow-primary',
  GLOW_SECONDARY: '--glow-secondary',
  STATUS_DOT: '--status-dot',
  TREND_UP: '--trend-up',
  TREND_DOWN: '--trend-down',
} as const;

export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error. Please check your connection.',
  API_ERROR: 'Failed to fetch data from the server.',
  CONFIG_ERROR: 'Failed to load configuration.',
  THEME_ERROR: 'Failed to apply theme.',
  WIFI_SETUP: 'Device is in WiFi setup mode.',
} as const;
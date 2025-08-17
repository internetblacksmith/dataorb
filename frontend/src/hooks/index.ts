// Export all custom hooks from a single location

export { useTheme } from './useTheme';
export { useKeyboardNavigation } from './useKeyboardNavigation';
export { useNetworkStatus } from './useNetworkStatus';
export { useStats } from './useStats';
export { useDisplayConfig } from './useDisplayConfig';
export { useInterval } from './useInterval';
export { useLocalStorage } from './useLocalStorage';

// Dashboard-specific hooks
export { useClassicDashboard } from './useClassicDashboard';
export { useModernDashboard } from './useModernDashboard';
export { useAnalyticsDashboard } from './useAnalyticsDashboard';
export { useExecutiveDashboard } from './useExecutiveDashboard';
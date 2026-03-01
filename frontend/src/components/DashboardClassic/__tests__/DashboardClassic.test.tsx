import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DashboardClassic from '../index';

// Mock CSS imports
jest.mock('../styles.css', () => ({}));
jest.mock('../../common/MetricCard/styles.css', () => ({}));
jest.mock('../../common/ErrorDisplay/styles.css', () => ({}));

// Mock hooks to isolate component rendering
const mockUseNetworkStatus = jest.fn();
const mockUseDisplayConfig = jest.fn();
const mockUseDashboardStats = jest.fn();
const mockUseTheme = jest.fn();

jest.mock('../../../hooks', () => ({
  useKeyboardNavigation: jest.fn(),
  useNetworkStatus: () => mockUseNetworkStatus(),
  useDisplayConfig: () => mockUseDisplayConfig(),
  useDashboardStats: () => mockUseDashboardStats(),
  useTheme: () => mockUseTheme(),
  useInterval: jest.fn(),
}));

const renderDashboard = () =>
  render(
    <MemoryRouter>
      <DashboardClassic />
    </MemoryRouter>,
  );

describe('DashboardClassic', () => {
  beforeEach(() => {
    mockUseNetworkStatus.mockReturnValue({ networkStatus: null, error: null });
    mockUseDisplayConfig.mockReturnValue({
      displayConfig: { theme: 'dark' },
      theme: 'dark',
    });
    mockUseTheme.mockReturnValue({ applyTheme: jest.fn() });
  });

  it('renders 3 metric cards with labels and values', async () => {
    mockUseDashboardStats.mockReturnValue({
      stats: {
        top: { label: 'Events', value: 142 },
        left: { label: 'Users', value: 37 },
        right: { label: 'Views', value: 89 },
        demo_mode: false,
      },
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderDashboard();
    expect(screen.getByText('Events')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('Views')).toBeInTheDocument();
  });

  it('shows Demo Mode when demo_mode is true', () => {
    mockUseDashboardStats.mockReturnValue({
      stats: {
        top: { label: 'Events', value: 142 },
        demo_mode: true,
      },
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderDashboard();
    expect(screen.getByText('Demo Mode')).toBeInTheDocument();
  });

  it('shows Live Data when not in demo mode', () => {
    mockUseDashboardStats.mockReturnValue({
      stats: {
        top: { label: 'Events', value: 100 },
        demo_mode: false,
      },
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderDashboard();
    expect(screen.getByText('Live Data')).toBeInTheDocument();
  });

  it('shows loading state before data arrives', () => {
    mockUseDashboardStats.mockReturnValue({
      stats: null,
      loading: true,
      error: null,
      refetch: jest.fn(),
    });

    renderDashboard();
    expect(screen.getByText('Loading DataOrb...')).toBeInTheDocument();
  });

  it('shows error state with retry', () => {
    mockUseDashboardStats.mockReturnValue({
      stats: null,
      loading: false,
      error: 'Failed to fetch',
      refetch: jest.fn(),
    });

    renderDashboard();
    expect(screen.getByText('Failed to fetch')).toBeInTheDocument();
    expect(screen.getByText('Retry')).toBeInTheDocument();
  });

  it('shows WiFi Setup Mode on wifi-setup-mode error', () => {
    mockUseNetworkStatus.mockReturnValue({
      networkStatus: null,
      error: 'wifi-setup-mode',
    });
    mockUseDashboardStats.mockReturnValue({
      stats: null,
      loading: false,
      error: null,
      refetch: jest.fn(),
    });

    renderDashboard();
    expect(screen.getByText('WiFi Setup Mode')).toBeInTheDocument();
  });
});

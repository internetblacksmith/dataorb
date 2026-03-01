import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import ConfigPage from '../index';

// Mock CSS
jest.mock('../styles.css', () => ({}));
jest.mock('../../common/LoadingSpinner/styles.css', () => ({}));

// Mock sub-components to avoid deep dependency chains
jest.mock('../PostHogConfig', () => ({
  PostHogConfig: () => <div data-testid="posthog-panel">PostHog Config Panel</div>,
}));
jest.mock('../DisplayConfig', () => ({
  DisplayConfig: () => <div data-testid="display-panel">Display Config Panel</div>,
}));
jest.mock('../NetworkConfig', () => ({
  NetworkConfig: () => <div data-testid="network-panel">Network Config Panel</div>,
}));
jest.mock('../ThemeConfig', () => ({
  ThemeConfig: () => <div data-testid="theme-panel">Theme Config Panel</div>,
}));
jest.mock('../OTAConfig', () => ({
  OTAConfig: () => <div data-testid="ota-panel">OTA Config Panel</div>,
}));

// Mock hooks
jest.mock('../../../hooks', () => ({
  useKeyboardNavigation: jest.fn(),
  useNetworkStatus: () => ({ networkStatus: null }),
  useTheme: () => ({ applyTheme: jest.fn() }),
}));

const mockConfig = {
  device_id: 'test-device',
  posthog: { api_key: 'test', project_id: '1' },
  display: { theme: 'dark', layout: 'classic' },
};

const renderConfigPage = () =>
  render(
    <MemoryRouter initialEntries={['/config']}>
      <ConfigPage />
    </MemoryRouter>,
  );

describe('ConfigPage', () => {
  beforeEach(() => {
    global.fetch = jest.fn().mockImplementation((url: string) => {
      if (url.includes('/api/admin/config')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockConfig),
        });
      }
      if (url.includes('/api/themes')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve([]),
        });
      }
      if (url.includes('/api/admin/ota/status')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ enabled: true }),
        });
      }
      if (url.includes('/api/metrics/available')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({}),
        });
      }
      return Promise.resolve({ ok: true, json: () => Promise.resolve({}) });
    });
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('renders all 5 tab buttons', async () => {
    renderConfigPage();
    await waitFor(() => {
      expect(screen.getByText('PostHog')).toBeInTheDocument();
    });
    expect(screen.getByText('Display')).toBeInTheDocument();
    expect(screen.getByText('Network')).toBeInTheDocument();
    expect(screen.getByText('Themes')).toBeInTheDocument();
    expect(screen.getByText('Updates')).toBeInTheDocument();
  });

  it('Save button sends POST to config endpoint', async () => {
    renderConfigPage();
    await waitFor(() => {
      expect(screen.getByText('Save Changes')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Save Changes'));

    await waitFor(() => {
      const postCalls = (global.fetch as jest.Mock).mock.calls.filter(
        ([url, opts]: [string, RequestInit?]) =>
          url.includes('/api/admin/config') && opts?.method === 'POST',
      );
      expect(postCalls.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows error when config load fails', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

    renderConfigPage();
    await waitFor(() => {
      expect(
        screen.getByText('Error Loading Configuration'),
      ).toBeInTheDocument();
    });
  });
});

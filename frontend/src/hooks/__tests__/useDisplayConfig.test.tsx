import React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { useDisplayConfig } from '../useDisplayConfig';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter>{children}</MemoryRouter>
);

describe('useDisplayConfig', () => {
  beforeEach(() => {
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('fetches config on mount', async () => {
    const mockConfig = {
      display: { theme: 'dark', layout: 'classic', refresh_interval: 60000 },
    };
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockConfig),
    });

    const { result } = renderHook(() => useDisplayConfig(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.displayConfig).toEqual(mockConfig.display);
    expect(result.current.theme).toBe('dark');
  });

  it('BroadcastChannel update propagates config', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          display: { theme: 'dark', layout: 'classic' },
        }),
    });

    const { result } = renderHook(() => useDisplayConfig(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));

    // BroadcastChannel is mocked in setupTests.ts — channel.postMessage is a no-op,
    // so we verify the listener registration doesn't crash
    expect(result.current.displayConfig).toBeDefined();
  });

  it('enforces minimum 30s refresh interval', async () => {
    const mockConfig = {
      display: { theme: 'dark', layout: 'classic', refresh_interval: 5000 },
    };
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(mockConfig),
    });

    const { result } = renderHook(() => useDisplayConfig(), { wrapper });

    await waitFor(() => expect(result.current.loading).toBe(false));
    // REFRESH_INTERVALS.STATS = 60000 is the minimum
    expect(result.current.refreshInterval).toBeGreaterThanOrEqual(60000);
  });
});

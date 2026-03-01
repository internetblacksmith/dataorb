import React from 'react';
import { renderHook, act, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { useDashboardStats } from '../useDashboardStats';

const wrapper = ({ children }: { children: React.ReactNode }) => (
  <MemoryRouter>{children}</MemoryRouter>
);

describe('useDashboardStats', () => {
  beforeEach(() => {
    jest.useFakeTimers();
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.useRealTimers();
    jest.restoreAllMocks();
  });

  it('starts with loading: true', () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      json: () => Promise.resolve({ top: { label: 'Events', value: 42 } }),
    });

    const { result } = renderHook(
      () => useDashboardStats('/api/stats/classic'),
      { wrapper },
    );

    expect(result.current.loading).toBe(true);
  });

  it('populates stats on successful fetch', async () => {
    const mockData = {
      top: { label: 'Events', value: 100 },
      demo_mode: false,
    };
    (global.fetch as jest.Mock).mockResolvedValue({
      json: () => Promise.resolve(mockData),
    });

    const { result } = renderHook(
      () => useDashboardStats('/api/stats/classic'),
      { wrapper },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.stats).toEqual(mockData);
    expect(result.current.error).toBeNull();
  });

  it('sets error on fetch failure', async () => {
    (global.fetch as jest.Mock).mockRejectedValue(new Error('Network error'));

    const { result } = renderHook(
      () => useDashboardStats('/api/stats/classic'),
      { wrapper },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBeTruthy();
    expect(result.current.stats).toBeNull();
  });

  it('sets error when API returns error field', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      json: () => Promise.resolve({ error: 'PostHog credentials not configured' }),
    });

    const { result } = renderHook(
      () => useDashboardStats('/api/stats/classic'),
      { wrapper },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toBe('PostHog credentials not configured');
  });

  it('handles network_lost error with redirect', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      json: () =>
        Promise.resolve({ error: 'network_lost', redirect: '/setup' }),
    });

    const { result } = renderHook(
      () => useDashboardStats('/api/stats/classic'),
      { wrapper },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));
    expect(result.current.error).toContain('Network connection lost');
  });

  it('enforces minimum 60s refresh interval', () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      json: () => Promise.resolve({ top: { label: 'Events', value: 1 } }),
    });

    // Pass a very short interval (10s)
    renderHook(() => useDashboardStats('/api/stats/classic', 10000), {
      wrapper,
    });

    // The initial fetch fires immediately
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Advance 30s — no second fetch should happen (min interval is 60s)
    act(() => jest.advanceTimersByTime(30000));
    expect(global.fetch).toHaveBeenCalledTimes(1);

    // Advance to 61s — now a second fetch
    act(() => jest.advanceTimersByTime(31000));
    expect(global.fetch).toHaveBeenCalledTimes(2);
  });

  it('refetch() triggers a new fetch', async () => {
    const mockData = { top: { label: 'Events', value: 1 } };
    (global.fetch as jest.Mock).mockResolvedValue({
      json: () => Promise.resolve(mockData),
    });

    const { result } = renderHook(
      () => useDashboardStats('/api/stats/classic'),
      { wrapper },
    );

    await waitFor(() => expect(result.current.loading).toBe(false));

    const callsBefore = (global.fetch as jest.Mock).mock.calls.length;
    await act(async () => {
      await result.current.refetch();
    });

    expect((global.fetch as jest.Mock).mock.calls.length).toBeGreaterThan(
      callsBefore,
    );
  });
});

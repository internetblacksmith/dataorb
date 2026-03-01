import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import DashboardRouter from '../index';

// Mock all dashboard components to verify which one renders
jest.mock('../../DashboardClassic', () => () => (
  <div data-testid="dashboard-classic">Classic</div>
));
jest.mock('../../DashboardModern', () => () => (
  <div data-testid="dashboard-modern">Modern</div>
));
jest.mock('../../DashboardAnalytics', () => () => (
  <div data-testid="dashboard-analytics">Analytics</div>
));
jest.mock('../../DashboardExecutive', () => () => (
  <div data-testid="dashboard-executive">Executive</div>
));

const renderRouter = () =>
  render(
    <MemoryRouter>
      <DashboardRouter />
    </MemoryRouter>,
  );

describe('DashboardRouter', () => {
  afterEach(() => {
    jest.restoreAllMocks();
  });

  it('defaults to Executive layout', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ display: {} }),
    });

    renderRouter();
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-executive')).toBeInTheDocument();
    });
  });

  it('renders Classic when config says classic', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ display: { layout: 'classic' } }),
    });

    renderRouter();
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-classic')).toBeInTheDocument();
    });
  });

  it('shows loading state while fetching config', () => {
    global.fetch = jest.fn(
      () => new Promise(() => {}), // never resolves
    );

    renderRouter();
    expect(screen.getByText('Loading Dashboard...')).toBeInTheDocument();
  });

  it('falls back to Executive on fetch error', async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

    renderRouter();
    await waitFor(() => {
      expect(screen.getByTestId('dashboard-executive')).toBeInTheDocument();
    });
  });
});

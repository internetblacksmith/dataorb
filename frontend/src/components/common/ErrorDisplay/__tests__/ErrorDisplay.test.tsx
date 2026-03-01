import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ErrorDisplay } from '../index';

// Mock the CSS import
jest.mock('../styles.css', () => ({}));

describe('ErrorDisplay', () => {
  it('shows DataOrb-Setup in WiFi setup mode', () => {
    render(<ErrorDisplay error="wifi-setup-mode" />);
    expect(screen.getByText('DataOrb-Setup')).toBeInTheDocument();
    expect(screen.getByText('WiFi Setup Mode')).toBeInTheDocument();
  });

  it('shows generic error message with retry button', () => {
    const onRetry = jest.fn();
    render(<ErrorDisplay error="Something went wrong" onRetry={onRetry} />);
    expect(screen.getByText('Something went wrong')).toBeInTheDocument();

    const retryBtn = screen.getByText('Retry');
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('hides retry button when showRetry is false', () => {
    render(
      <ErrorDisplay
        error="Something went wrong"
        onRetry={() => {}}
        showRetry={false}
      />,
    );
    expect(screen.queryByText('Retry')).not.toBeInTheDocument();
  });
});

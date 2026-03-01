import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MetricCard } from '../index';

// Mock the CSS import
jest.mock('../styles.css', () => ({}));

describe('MetricCard', () => {
  it('renders formatted value and label', () => {
    render(<MetricCard value={1500} label="Events" />);
    expect(screen.getByText('1.5K')).toBeInTheDocument();
    expect(screen.getByText('Events')).toBeInTheDocument();
  });

  it('applies position CSS class', () => {
    const { container } = render(
      <MetricCard value={42} label="Users" position="top" />,
    );
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('metric-top');
  });

  it('fires onClick handler', () => {
    const handleClick = jest.fn();
    render(<MetricCard value={10} label="Views" onClick={handleClick} />);
    fireEvent.click(screen.getByText('10'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });
});

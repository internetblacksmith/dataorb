import React from 'react';
import { formatNumber } from '../../../utils';
import './styles.css';

interface MetricCardProps {
  value: number;
  label: string;
  position?: 'top' | 'left' | 'right' | 'bottom';
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = React.memo(({
  value,
  label,
  position,
  size = 'medium',
  onClick,
}) => {
  return (
    <div
      className={`metric-card metric-${size} ${position ? `metric-${position}` : ''} ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      <div className="metric-value">{formatNumber(value)}</div>
      <div className="metric-label">{label}</div>
    </div>
  );
});

MetricCard.displayName = 'MetricCard';

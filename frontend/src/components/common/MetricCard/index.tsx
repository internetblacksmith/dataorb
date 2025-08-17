import React from 'react';
import { formatNumber, getTrendIcon, getTrendClass } from '../../../utils';
import './styles.css';

interface MetricCardProps {
  value: number;
  label: string;
  trend?: number;
  icon?: string;
  position?: 'top' | 'left' | 'right' | 'bottom';
  size?: 'small' | 'medium' | 'large';
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = React.memo(({
  value,
  label,
  trend,
  icon,
  position,
  size = 'medium',
  onClick,
}) => {
  const formattedValue = formatNumber(value);
  const trendIcon = getTrendIcon(trend);
  const trendClass = getTrendClass(trend);

  return (
    <div 
      className={`metric-card metric-${size} ${position ? `metric-${position}` : ''} ${onClick ? 'clickable' : ''}`}
      onClick={onClick}
    >
      {icon && <div className="metric-icon">{icon}</div>}
      <div className="metric-value">{formattedValue}</div>
      <div className="metric-label">{label}</div>
      {trend !== undefined && (
        <div className={`metric-trend ${trendClass}`}>
          <span className="trend-icon">{trendIcon}</span>
          <span className="trend-value">{Math.abs(trend).toFixed(1)}%</span>
        </div>
      )}
    </div>
  );
});

MetricCard.displayName = 'MetricCard';
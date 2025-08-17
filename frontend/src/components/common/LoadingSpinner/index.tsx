import React from 'react';
import './styles.css';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = React.memo(({ 
  size = 'medium', 
  message = 'Loading...' 
}) => {
  return (
    <div className={`loading-container loading-${size}`}>
      <div className="loading-spinner" />
      {message && <p className="loading-message">{message}</p>}
    </div>
  );
});

LoadingSpinner.displayName = 'LoadingSpinner';
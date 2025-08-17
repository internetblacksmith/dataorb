import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { KEYBOARD_SHORTCUTS } from '../constants';

/**
 * Custom hook for keyboard navigation shortcuts
 */
export const useKeyboardNavigation = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Check for Ctrl+Alt combinations
      if (e.ctrlKey && e.altKey) {
        e.preventDefault(); // Prevent default browser behavior
        switch (e.key) {
          case KEYBOARD_SHORTCUTS.DASHBOARD_CLASSIC.key:
            navigate('/classic');
            break;
          case KEYBOARD_SHORTCUTS.DASHBOARD_MODERN.key:
            navigate('/modern');
            break;
          case KEYBOARD_SHORTCUTS.DASHBOARD_ANALYTICS.key:
            navigate('/analytics');
            break;
          case KEYBOARD_SHORTCUTS.DASHBOARD_EXECUTIVE.key:
            navigate('/executive');
            break;
          case KEYBOARD_SHORTCUTS.CONFIG.key:
            navigate('/config');
            break;
        }
      }
      
      // Check for Ctrl+Shift+C combination
      if (e.ctrlKey && e.shiftKey && e.key === KEYBOARD_SHORTCUTS.CONFIG_ALTERNATE.key) {
        e.preventDefault();
        navigate('/config');
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [navigate]);
};
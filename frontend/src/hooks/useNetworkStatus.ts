import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { NetworkStatus } from '../types';
import { API_ENDPOINTS } from '../constants';
import { isAPNetwork, isLocalDisplay } from '../utils';

/**
 * Custom hook for network status management
 */
export const useNetworkStatus = () => {
  const navigate = useNavigate();
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus | null>(null);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const checkNetworkStatus = useCallback(async () => {
    if (isChecking) return;
    
    setIsChecking(true);
    setError(null);

    try {
      const response = await fetch(API_ENDPOINTS.NETWORK_STATUS);
      
      if (!response.ok) {
        throw new Error('Failed to fetch network status');
      }

      const data: NetworkStatus = await response.json();
      setNetworkStatus(data);

      // Handle AP mode redirection
      if (data.ap_mode) {
        if (isAPNetwork()) {
          // Redirect to setup page if on AP network
          navigate('/setup');
        } else if (isLocalDisplay()) {
          // Set error for local display
          setError('wifi-setup-mode');
        }
      }

      return data;
    } catch (err) {
      setError('Failed to check network status');
      return null;
    } finally {
      setIsChecking(false);
    }
  }, [navigate, isChecking]);

  // Check network status on mount
  useEffect(() => {
    checkNetworkStatus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    networkStatus,
    isChecking,
    error,
    checkNetworkStatus,
    isInAPMode: networkStatus?.ap_mode || false,
    isConnected: networkStatus?.connected || false,
  };
};
import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { NetworkStatus } from '../types';
import { API_ENDPOINTS } from '../constants';
import { isAPNetwork, isLocalDisplay } from '../utils';

export const useNetworkStatus = () => {
  const navigate = useNavigate();
  const [networkStatus, setNetworkStatus] = useState<NetworkStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const isCheckingRef = useRef(false);

  const checkNetworkStatus = useCallback(async () => {
    if (isCheckingRef.current) return;

    isCheckingRef.current = true;
    setError(null);

    try {
      const response = await fetch(API_ENDPOINTS.NETWORK_STATUS);

      if (!response.ok) {
        throw new Error('Failed to fetch network status');
      }

      const data: NetworkStatus = await response.json();
      setNetworkStatus(data);

      if (data.ap_mode) {
        if (isAPNetwork()) {
          navigate('/setup');
        } else if (isLocalDisplay()) {
          setError('wifi-setup-mode');
        }
      }

      return data;
    } catch {
      setError('Failed to check network status');
      return null;
    } finally {
      isCheckingRef.current = false;
    }
  }, [navigate]);

  useEffect(() => {
    checkNetworkStatus();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return {
    networkStatus,
    error,
    checkNetworkStatus,
    isInAPMode: networkStatus?.ap_mode || false,
    isConnected: networkStatus?.connected || false,
  };
};

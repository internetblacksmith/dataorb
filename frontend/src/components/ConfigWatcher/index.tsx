import { useEffect, useRef } from 'react';

const CONFIG_CHECK_INTERVAL = 5000; // Check every 5 seconds

export function ConfigWatcher() {
  const configVersionRef = useRef<string | null>(null);
  const isFirstCheckRef = useRef(true);

  useEffect(() => {
    const checkConfigVersion = async () => {
      try {
        const response = await fetch('/api/config/version');
        if (!response.ok) {
          if (process.env.NODE_ENV === 'development') {
            // eslint-disable-next-line no-console
            console.error('Failed to fetch config version');
          }
          return;
        }

        const data = await response.json();
        const newVersion = data.version;

        // Skip reload on first check (initial load)
        if (isFirstCheckRef.current) {
          configVersionRef.current = newVersion;
          isFirstCheckRef.current = false;
          // Only log in development
          if (process.env.NODE_ENV === 'development') {
            // eslint-disable-next-line no-console
            console.log(`Config version initialized: ${newVersion}`);
          }
          return;
        }

        // Check if config has changed
        if (configVersionRef.current && configVersionRef.current !== newVersion) {
          if (process.env.NODE_ENV === 'development') {
            // eslint-disable-next-line no-console
            console.log(`Config changed from ${configVersionRef.current} to ${newVersion}, reloading...`);
          }
          // Small delay to ensure config is fully saved
          setTimeout(() => {
            window.location.reload();
          }, 500);
        }

        configVersionRef.current = newVersion;
      } catch (error) {
        if (process.env.NODE_ENV === 'development') {
          // eslint-disable-next-line no-console
          console.error('Error checking config version:', error);
        }
      }
    };

    // Initial check after a short delay
    const initialTimeout = setTimeout(() => {
      checkConfigVersion();
    }, 1000);

    // Set up interval for subsequent checks
    const interval = setInterval(checkConfigVersion, CONFIG_CHECK_INTERVAL);

    // Cleanup
    return () => {
      clearTimeout(initialTimeout);
      clearInterval(interval);
    };
  }, []);

  // This component doesn't render anything
  return null;
}

export default ConfigWatcher;
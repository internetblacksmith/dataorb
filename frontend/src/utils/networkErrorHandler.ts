/**
 * Handle network error responses from the API
 * Checks for network_lost error and redirects to setup page
 */
export const handleNetworkError = (data: any, setError: (error: string | null) => void, setStats: (stats: any) => void) => {
  if (data.error === 'network_lost' && data.redirect) {
    // Show message briefly then redirect
    setError('Network connection lost. Starting setup mode...');
    setStats(null);
    setTimeout(() => {
      window.location.href = data.redirect;
    }, 2000);
    return true; // Handled
  }
  return false; // Not a network error
};
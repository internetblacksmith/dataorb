export const handleNetworkError = (data: Record<string, unknown>, setError: (error: string | null) => void, setStats: (stats: null) => void) => {
  if (data.error === 'network_lost' && typeof data.redirect === 'string' && data.redirect.startsWith('/')) {
    setError('Network connection lost. Starting setup mode...');
    setStats(null);
    setTimeout(() => {
      window.location.href = data.redirect as string;
    }, 2000);
    return true;
  }
  return false;
};

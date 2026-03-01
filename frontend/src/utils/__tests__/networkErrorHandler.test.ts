import { handleNetworkError } from '../networkErrorHandler';

describe('handleNetworkError', () => {
  let setError: jest.Mock;
  let setStats: jest.Mock;

  beforeEach(() => {
    setError = jest.fn();
    setStats = jest.fn();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('handles network_lost with valid /setup redirect', () => {
    const data = { error: 'network_lost', redirect: '/setup' };
    const result = handleNetworkError(data, setError, setStats);

    expect(result).toBe(true);
    expect(setError).toHaveBeenCalledWith(
      expect.stringContaining('Network connection lost'),
    );
    expect(setStats).toHaveBeenCalledWith(null);
  });

  it('ignores non-network errors', () => {
    const data = { error: 'some_other_error' };
    const result = handleNetworkError(data, setError, setStats);
    expect(result).toBe(false);
  });

  it('rejects external URL redirect (open redirect guard)', () => {
    const data = {
      error: 'network_lost',
      redirect: 'https://evil.com/steal',
    };
    const result = handleNetworkError(data, setError, setStats);
    expect(result).toBe(false);
  });

  it('returns false when redirect field is missing', () => {
    const data = { error: 'network_lost' };
    const result = handleNetworkError(data, setError, setStats);
    expect(result).toBe(false);
  });
});

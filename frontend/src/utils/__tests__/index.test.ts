import {
  formatNumber,
  formatTime,
  formatDate,
  isLocalDisplay,
  isAPNetwork,
} from '../index';

// ---------------------------------------------------------------------------
// formatNumber
// ---------------------------------------------------------------------------

describe('formatNumber', () => {
  it('returns plain number for values under 1000', () => {
    expect(formatNumber(142)).toBe('142');
  });

  it('formats thousands with K suffix', () => {
    expect(formatNumber(1500)).toBe('1.5K');
  });

  it('formats millions with M suffix', () => {
    expect(formatNumber(2500000)).toBe('2.5M');
  });

  it('formats exactly 1000 as 1.0K', () => {
    expect(formatNumber(1000)).toBe('1.0K');
  });

  it('formats exactly 1000000 as 1.0M', () => {
    expect(formatNumber(1000000)).toBe('1.0M');
  });
});

// ---------------------------------------------------------------------------
// formatTime / formatDate
// ---------------------------------------------------------------------------

describe('formatTime', () => {
  it('returns HH:MM:SS format', () => {
    const date = new Date('2024-06-15T14:30:45');
    const result = formatTime(date);
    expect(result).toMatch(/^\d{2}:\d{2}:\d{2}$/);
  });
});

describe('formatDate', () => {
  it('returns weekday + month + day', () => {
    const date = new Date('2024-01-15');
    const result = formatDate(date);
    // Expect format like "Mon, Jan 15"
    expect(result).toMatch(/\w+,\s\w+\s\d+/);
  });
});

// ---------------------------------------------------------------------------
// isLocalDisplay / isAPNetwork
// ---------------------------------------------------------------------------

describe('isLocalDisplay', () => {
  const originalLocation = window.location;

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
    });
  });

  it('returns true for localhost', () => {
    Object.defineProperty(window, 'location', {
      value: { hostname: 'localhost' },
      writable: true,
    });
    expect(isLocalDisplay()).toBe(true);
  });

  it('returns false for a remote host', () => {
    Object.defineProperty(window, 'location', {
      value: { hostname: '192.168.1.100' },
      writable: true,
    });
    expect(isLocalDisplay()).toBe(false);
  });
});

describe('isAPNetwork', () => {
  const originalLocation = window.location;

  afterEach(() => {
    Object.defineProperty(window, 'location', {
      value: originalLocation,
      writable: true,
    });
  });

  it('returns true for 192.168.4.1', () => {
    Object.defineProperty(window, 'location', {
      value: { hostname: '192.168.4.1' },
      writable: true,
    });
    expect(isAPNetwork()).toBe(true);
  });

  it('returns false for other subnets', () => {
    Object.defineProperty(window, 'location', {
      value: { hostname: '192.168.1.1' },
      writable: true,
    });
    expect(isAPNetwork()).toBe(false);
  });
});

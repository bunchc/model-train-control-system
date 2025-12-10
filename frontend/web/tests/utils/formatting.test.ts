import { formatRelativeTime } from '../../src/utils/formatting';

describe('formatRelativeTime', () => {
  it('returns "Just now" for timestamps <1 min ago', () => {
    const now = new Date();
    const lessThanOneMinAgo = new Date(now.getTime() - 30 * 1000).toISOString();
    expect(formatRelativeTime(lessThanOneMinAgo)).toBe('Just now');
  });

  it('returns formatted date for timestamps >=1 min ago', () => {
    const now = new Date();
    const twoMinAgo = new Date(now.getTime() - 2 * 60 * 1000).toISOString();
    const formatted = formatRelativeTime(twoMinAgo);
    expect(formatted).toMatch(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}/);
  });

  it('returns "Never" for null/undefined', () => {
    expect(formatRelativeTime(null as any)).toBe('Never');
    expect(formatRelativeTime(undefined as any)).toBe('Never');
  });

  it('returns "Never" for future timestamps', () => {
    const now = new Date();
    const future = new Date(now.getTime() + 60 * 60 * 1000).toISOString();
    expect(formatRelativeTime(future)).toBe('Never');
  });

  it('handles malformed date strings gracefully', () => {
    expect(formatRelativeTime('not-a-date')).toBe('Never');
  });
});

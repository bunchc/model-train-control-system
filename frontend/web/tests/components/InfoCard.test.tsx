import { describe, it, expect } from 'vitest';
import { screen } from '@testing-library/react';
import { render } from '../utils/test-utils';
import { InfoCard } from '@/components/common/InfoCard';

describe('InfoCard', () => {
  it('renders title correctly', () => {
    render(<InfoCard title="Controller Info" items={[]} />);

    expect(
      screen.getByRole('heading', { name: /controller info/i })
    ).toBeInTheDocument();
  });

  it('renders all items with labels and values', () => {
    const items = [
      { label: 'Name', value: 'Pi-01' },
      { label: 'Port', value: 8080 },
      { label: 'Status', value: 'online' },
    ];

    render(<InfoCard title="Details" items={items} />);

    // Check labels
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Port')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();

    // Check values
    expect(screen.getByText('Pi-01')).toBeInTheDocument();
    expect(screen.getByText('8080')).toBeInTheDocument();
    expect(screen.getByText('online')).toBeInTheDocument();
  });

  it('displays "--" for null values', () => {
    const items = [{ label: 'Version', value: null }];

    render(<InfoCard title="Test" items={items} />);

    expect(screen.getByText('--')).toBeInTheDocument();
  });

  it('displays "--" for undefined values', () => {
    const items = [{ label: 'Address', value: undefined }];

    render(<InfoCard title="Test" items={items} />);

    expect(screen.getByText('--')).toBeInTheDocument();
  });

  it('applies monospace font when mono: true', () => {
    const items = [{ label: 'ID', value: 'abc-123-def', mono: true }];

    render(<InfoCard title="Test" items={items} />);

    const valueElement = screen.getByText('abc-123-def');
    expect(valueElement).toHaveClass('font-mono');
  });

  it('does not apply monospace font when mono is false or omitted', () => {
    const items = [
      { label: 'Name', value: 'Test Value', mono: false },
      { label: 'Other', value: 'Another Value' },
    ];

    render(<InfoCard title="Test" items={items} />);

    const testValue = screen.getByText('Test Value');
    const anotherValue = screen.getByText('Another Value');

    expect(testValue).not.toHaveClass('font-mono');
    expect(anotherValue).not.toHaveClass('font-mono');
  });

  it('handles empty items array gracefully', () => {
    render(<InfoCard title="Empty Card" items={[]} />);

    // Title should render
    expect(
      screen.getByRole('heading', { name: /empty card/i })
    ).toBeInTheDocument();

    // No definition list should be present
    expect(screen.queryByRole('definition')).not.toBeInTheDocument();
  });

  it('accepts custom className prop', () => {
    const { container } = render(
      <InfoCard title="Test" items={[]} className="mt-4 custom-class" />
    );

    const section = container.querySelector('section');
    expect(section).toHaveClass('custom-class');
    expect(section).toHaveClass('mt-4');
    // Also verify default classes are preserved
    expect(section).toHaveClass('rounded-lg');
  });
});

import React, { useId } from 'react';
import { cn } from '@/utils/cn';

export interface InfoCardItem {
  label: string;
  value: string | number | null | undefined;
  /** Use monospace font for UUIDs, hashes, or technical identifiers */
  mono?: boolean;
}

export interface InfoCardProps {
  /** Card title displayed as heading */
  title: string;
  /** Array of label/value pairs to display */
  items: InfoCardItem[];
  /** Additional CSS classes for the container */
  className?: string;
}

/**
 * A reusable card component for displaying label/value pairs.
 * Commonly used for showing entity details like controller info,
 * configuration settings, or metadata.
 *
 * @example
 * <InfoCard
 *   title="Controller Info"
 *   items={[
 *     { label: 'Name', value: controller.name },
 *     { label: 'ID', value: controller.id, mono: true },
 *     { label: 'Version', value: controller.version },
 *   ]}
 * />
 */
export const InfoCard: React.FC<InfoCardProps> = ({ title, items, className }) => {
  const titleId = useId();

  return (
    <section
      aria-labelledby={titleId}
      className={cn(
        'rounded-lg bg-white p-4 shadow-sm dark:bg-gray-800',
        className
      )}
    >
      <h3
        id={titleId}
        className="text-lg font-semibold text-gray-900 dark:text-gray-100"
      >
        {title}
      </h3>

      {items.length > 0 && (
        <dl className="mt-3 space-y-2">
          {items.map((item, index) => (
            <div key={index} className="flex justify-between text-sm">
              <dt className="text-gray-600 dark:text-gray-400">{item.label}</dt>
              <dd
                className={cn(
                  'font-medium text-gray-900 dark:text-gray-100',
                  item.mono && 'font-mono'
                )}
                data-testid={item["data-testid"]}
              >
                {item.value ?? '--'}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
};

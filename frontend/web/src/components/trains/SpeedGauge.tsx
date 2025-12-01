import React from 'react';

export interface SpeedGaugeProps {
  speed: number;
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Circular speed gauge component
 */
export const SpeedGauge: React.FC<SpeedGaugeProps> = ({ speed, size = 'md' }) => {
  const sizes = {
    sm: { width: 80, strokeWidth: 6, fontSize: '1rem' },
    md: { width: 120, strokeWidth: 8, fontSize: '1.5rem' },
    lg: { width: 160, strokeWidth: 10, fontSize: '2rem' },
  };

  const { width, strokeWidth, fontSize } = sizes[size];
  const radius = (width - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (speed / 100) * circumference;

  // Color based on speed
  const getColor = () => {
    if (speed === 0) return 'text-gray-400';
    if (speed < 30) return 'text-green-500';
    if (speed < 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={width} height={width} className="transform -rotate-90">
        {/* Background circle */}
        <circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx={width / 2}
          cy={width / 2}
          r={radius}
          stroke="currentColor"
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className={`transition-all duration-500 ${getColor()}`}
        />
      </svg>
      {/* Speed value */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`font-bold ${getColor()}`} style={{ fontSize }}>
          {speed}
        </span>
        <span className="text-xs text-gray-500 dark:text-gray-400">%</span>
      </div>
    </div>
  );
};

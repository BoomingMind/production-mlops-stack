'use client';

import { getAQICategoryInfo, getAQIColor } from '@/lib/api';

export function AQIGauge({ value, size = 'lg' }) {
  const color = getAQIColor(value);
  const maxAQI = 500;
  const percentage = Math.min((value / maxAQI) * 100, 100);
  const rotation = (percentage / 100) * 180 - 90;

  const sizes = {
    sm: { width: 120, height: 70, fontSize: 'text-xl', labelSize: 'text-xs' },
    md: { width: 160, height: 90, fontSize: 'text-2xl', labelSize: 'text-sm' },
    lg: { width: 220, height: 120, fontSize: 'text-4xl', labelSize: 'text-sm' },
    xl: { width: 280, height: 150, fontSize: 'text-5xl', labelSize: 'text-base' },
  };

  const { width, height, fontSize, labelSize } = sizes[size];

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width, height }}>
        {/* Background arc */}
        <svg
          viewBox="0 0 200 100"
          className="w-full h-full"
          style={{ overflow: 'visible' }}
        >
          {/* Background track */}
          <path
            d="M 10 100 A 90 90 0 0 1 190 100"
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="12"
            strokeLinecap="round"
            className="dark:stroke-gray-700"
          />
          {/* Colored arc */}
          <path
            d="M 10 100 A 90 90 0 0 1 190 100"
            fill="none"
            stroke={color}
            strokeWidth="12"
            strokeLinecap="round"
            strokeDasharray={`${percentage * 2.83} 283`}
            style={{
              transition: 'stroke-dasharray 0.5s ease-in-out',
            }}
          />
          {/* Needle */}
          <g
            style={{
              transform: `rotate(${rotation}deg)`,
              transformOrigin: '100px 100px',
              transition: 'transform 0.5s ease-in-out',
            }}
          >
            <line
              x1="100"
              y1="100"
              x2="100"
              y2="25"
              stroke={color}
              strokeWidth="3"
              strokeLinecap="round"
            />
            <circle cx="100" cy="100" r="6" fill={color} />
          </g>
        </svg>
        {/* Value display */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-end pb-0"
          style={{ top: '30%' }}
        >
          <span
            className={`font-bold ${fontSize}`}
            style={{ color }}
          >
            {Math.round(value)}
          </span>
          <span className={`text-gray-500 dark:text-gray-400 ${labelSize}`}>
            AQI
          </span>
        </div>
      </div>
      {/* Scale labels */}
      <div className="flex justify-between w-full mt-1 px-2">
        <span className="text-xs text-gray-400">0</span>
        <span className="text-xs text-gray-400">250</span>
        <span className="text-xs text-gray-400">500</span>
      </div>
    </div>
  );
}

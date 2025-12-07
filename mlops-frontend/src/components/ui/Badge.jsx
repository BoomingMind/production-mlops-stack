'use client';

import { cn } from '@/lib/utils';

const variants = {
  default: 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-100',
  success: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-100',
  warning: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-100',
  danger: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-100',
  info: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-100',
  purple: 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-100',
  orange: 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-100',
};

export function Badge({ className, variant = 'default', children, ...props }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}

export function AQIBadge({ category, className }) {
  const variantMap = {
    'Good': 'success',
    'Moderate': 'warning',
    'Unhealthy for Sensitive Groups': 'orange',
    'Unhealthy': 'danger',
    'Very Unhealthy': 'purple',
    'Hazardous': 'danger',
  };

  return (
    <Badge variant={variantMap[category] || 'default'} className={className}>
      {category}
    </Badge>
  );
}

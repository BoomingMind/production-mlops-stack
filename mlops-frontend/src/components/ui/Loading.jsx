'use client';

import { cn } from '@/lib/utils';

export function Loading({ className, size = 'md' }) {
  const sizes = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-2',
    lg: 'h-12 w-12 border-3',
    xl: 'h-16 w-16 border-4',
  };

  return (
    <div
      className={cn(
        'animate-spin rounded-full border-gray-300 border-t-blue-600',
        sizes[size],
        className
      )}
    />
  );
}

export function LoadingCard({ message = 'Loading...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-12">
      <Loading size="lg" />
      <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">{message}</p>
    </div>
  );
}

export function Skeleton({ className }) {
  return (
    <div
      className={cn(
        'animate-pulse rounded-md bg-gray-200 dark:bg-gray-700',
        className
      )}
    />
  );
}

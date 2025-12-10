'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { AQIBadge } from '@/components/ui/Badge';
import { getAQIColor, getAQICategoryInfo } from '@/lib/api';
import { TrendingUp, TrendingDown, Minus, BarChart3 } from 'lucide-react';

export function StatsCard({ stats, isLoading }) {
  if (isLoading) {
    return (
      <Card className="col-span-full lg:col-span-1">
        <CardHeader>
          <CardTitle>Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!stats) {
    return null;
  }

  const { 
    average_aqi, min_aqi, max_aqi, std_deviation,
    calculated_aqi_average, calculated_aqi_min, calculated_aqi_max, calculated_aqi_std_deviation
  } = stats;

  const aqiIndexStats = [
    {
      label: 'Average AQI',
      value: average_aqi,
      icon: BarChart3,
      color: getAQIColor(average_aqi),
    },
    {
      label: 'Minimum',
      value: min_aqi,
      icon: TrendingDown,
      color: getAQIColor(min_aqi),
    },
    {
      label: 'Maximum',
      value: max_aqi,
      icon: TrendingUp,
      color: getAQIColor(max_aqi),
    },
    {
      label: 'Std Deviation',
      value: std_deviation,
      icon: Minus,
      color: '#6b7280',
    },
  ];

  const calculatedAqiStats = [
    {
      label: 'Average AQI',
      value: calculated_aqi_average,
      icon: BarChart3,
      color: getAQIColor(calculated_aqi_average),
    },
    {
      label: 'Minimum',
      value: calculated_aqi_min,
      icon: TrendingDown,
      color: getAQIColor(calculated_aqi_min),
    },
    {
      label: 'Maximum',
      value: calculated_aqi_max,
      icon: TrendingUp,
      color: getAQIColor(calculated_aqi_max),
    },
    {
      label: 'Std Deviation',
      value: calculated_aqi_std_deviation,
      icon: Minus,
      color: '#6b7280',
    },
  ];

  return (
    <Card className="col-span-full lg:col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5" />
          Forecast Statistics
        </CardTitle>
        <CardDescription>Summary of predicted AQI values</CardDescription>
      </CardHeader>
      <CardContent>
        {/* AQI Index Statistics */}
        <div className="mb-4">
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
            AQI Index
          </h4>
          <div className="grid grid-cols-2 gap-3">
            {aqiIndexStats.map((item) => (
              <div
                key={item.label}
                className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50"
              >
                <div className="flex items-center gap-2 mb-1">
                  <item.icon className="w-3 h-3 text-gray-500" />
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {item.label}
                  </span>
                </div>
                <span
                  className="text-xl font-bold"
                  style={{ color: item.color }}
                >
                  {Math.round(item.value)}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Calculated AQI Statistics */}
        <div>
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-2">
            Calculated AQI
          </h4>
          <div className="grid grid-cols-2 gap-3">
            {calculatedAqiStats.map((item) => (
              <div
                key={item.label}
                className="p-3 rounded-lg bg-gray-50 dark:bg-gray-800/50"
              >
                <div className="flex items-center gap-2 mb-1">
                  <item.icon className="w-3 h-3 text-gray-500" />
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {item.label}
                  </span>
                </div>
                <span
                  className="text-xl font-bold"
                  style={{ color: item.color }}
                >
                  {Math.round(item.value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

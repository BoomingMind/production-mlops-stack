'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { AQIBadge } from '@/components/ui/Badge';
import { getAQIColor } from '@/lib/api';
import { formatTime } from '@/lib/utils';
import { Clock, ChevronRight } from 'lucide-react';

export function HourlyForecast({ predictions, isLoading, maxItems = 12 }) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Hourly Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="flex-shrink-0 w-20 h-24 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"
              />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!predictions || predictions.length === 0) {
    return null;
  }

  const displayPredictions = predictions.slice(0, maxItems);

  return (
    <Card className="col-span-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5" />
              Hourly Forecast
            </CardTitle>
            <CardDescription>
              Next {displayPredictions.length} hours
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex gap-3 overflow-x-auto pb-2 scrollbar-thin">
          {displayPredictions.map((prediction, index) => {
            const color = getAQIColor(prediction.predicted_aqi_index);
            const isNow = index === 0;

            return (
              <div
                key={prediction.datetime}
                className={`flex-shrink-0 flex flex-col items-center p-3 rounded-lg transition-all ${
                  isNow
                    ? 'bg-blue-50 dark:bg-blue-900/20 ring-2 ring-blue-500'
                    : 'bg-gray-50 dark:bg-gray-800/50 hover:bg-gray-100 dark:hover:bg-gray-800'
                }`}
                style={{ minWidth: '80px' }}
              >
                <span
                  className={`text-xs font-medium ${
                    isNow ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {isNow ? 'Next' : formatTime(prediction.datetime)}
                </span>
                <div
                  className="my-2 text-2xl font-bold"
                  style={{ color }}
                >
                  {Math.round(prediction.predicted_aqi_index)}
                </div>
                <div
                  className="w-full h-1 rounded-full"
                  style={{ backgroundColor: color }}
                />
                <span className="mt-1 text-xs text-gray-400 text-center leading-tight">
                  {prediction.aqi_category.split(' ')[0]}
                </span>
              </div>
            );
          })}
          {predictions.length > maxItems && (
            <div className="flex-shrink-0 flex items-center justify-center px-4 text-gray-400">
              <ChevronRight className="w-5 h-5" />
              <span className="text-sm">+{predictions.length - maxItems} more</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

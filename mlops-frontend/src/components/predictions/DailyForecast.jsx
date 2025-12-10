'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { AQIBadge } from '@/components/ui/Badge';
import { getAQIColor } from '@/lib/api';
import { formatDate } from '@/lib/utils';
import { Calendar, TrendingUp, TrendingDown } from 'lucide-react';

export function DailyForecast({ dailySummary, isLoading }) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Daily Forecast</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {Array.from({ length: 3 }).map((_, i) => (
              <div
                key={i}
                className="h-20 bg-gray-200 dark:bg-gray-700 rounded-lg animate-pulse"
              />
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!dailySummary || dailySummary.length === 0) {
    return null;
  }

  return (
    <Card className="col-span-full lg:col-span-1">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Calendar className="w-5 h-5" />
          Daily Forecast
        </CardTitle>
        <CardDescription>
          Next {dailySummary.length} days summary
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {dailySummary.map((day, index) => {
            const avgAqiIndex = day.aqi_index.mean;
            const avgCalculatedAqi = day.calculated_aqi.mean;
            const colorIndex = getAQIColor(avgAqiIndex);
            const colorCalculated = getAQIColor(avgCalculatedAqi);
            const isToday = index === 0;

            return (
              <div
                key={day.date}
                className={`p-4 rounded-lg transition-all ${
                  isToday
                    ? 'bg-blue-50 dark:bg-blue-900/20 ring-1 ring-blue-200 dark:ring-blue-800'
                    : 'bg-gray-50 dark:bg-gray-800/50'
                }`}
              >
                {/* Date Header */}
                <div className="flex items-center justify-between mb-3">
                  <div className="text-center min-w-[60px]">
                    <p className={`text-sm font-medium ${isToday ? 'text-blue-600 dark:text-blue-400' : 'text-gray-900 dark:text-white'}`}>
                      {isToday ? 'Today' : formatDate(day.date)}
                    </p>
                    {!isToday && (
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' })}
                      </p>
                    )}
                  </div>
                  <AQIBadge category={day.aqi_category} className="hidden sm:inline-flex" />
                </div>

                {/* AQI Index Row */}
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                    AQI Index
                  </span>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <div className="flex flex-col items-center">
                        <TrendingDown className="w-3 h-3 text-green-500" />
                        <span className="text-xs text-gray-500">{Math.round(day.aqi_index.min)}</span>
                      </div>
                      <div
                        className="w-16 h-2 rounded-full bg-gradient-to-r"
                        style={{
                          background: `linear-gradient(to right, ${getAQIColor(day.aqi_index.min)}, ${getAQIColor(day.aqi_index.max)})`,
                        }}
                      />
                      <div className="flex flex-col items-center">
                        <TrendingUp className="w-3 h-3 text-red-500" />
                        <span className="text-xs text-gray-500">{Math.round(day.aqi_index.max)}</span>
                      </div>
                    </div>
                    <span
                      className="text-lg font-bold"
                      style={{ color: colorIndex }}
                    >
                      {Math.round(avgAqiIndex)}
                    </span>
                  </div>
                </div>

                {/* Calculated AQI Row */}
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-500 dark:text-gray-400 font-medium">
                    Calculated AQI
                  </span>
                  <div className="flex items-center gap-3">
                    <div className="flex items-center gap-2">
                      <div className="flex flex-col items-center">
                        <TrendingDown className="w-3 h-3 text-green-500" />
                        <span className="text-xs text-gray-500">{Math.round(day.calculated_aqi.min)}</span>
                      </div>
                      <div
                        className="w-16 h-2 rounded-full bg-gradient-to-r"
                        style={{
                          background: `linear-gradient(to right, ${getAQIColor(day.calculated_aqi.min)}, ${getAQIColor(day.calculated_aqi.max)})`,
                        }}
                      />
                      <div className="flex flex-col items-center">
                        <TrendingUp className="w-3 h-3 text-red-500" />
                        <span className="text-xs text-gray-500">{Math.round(day.calculated_aqi.max)}</span>
                      </div>
                    </div>
                    <span
                      className="text-lg font-bold"
                      style={{ color: colorCalculated }}
                    >
                      {Math.round(avgCalculatedAqi)}
                    </span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

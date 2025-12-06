'use client';

import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { AQIBadge } from '@/components/ui/Badge';
import { AQIGauge } from './AQIGauge';
import { getAQICategoryInfo } from '@/lib/api';
import { formatDateTime } from '@/lib/utils';
import { Clock, AlertTriangle, CheckCircle2, Wind } from 'lucide-react';

export function CurrentAQICard({ prediction, isLoading }) {
  if (isLoading) {
    return (
      <Card className="col-span-full lg:col-span-1">
        <CardHeader>
          <CardTitle>Current AQI</CardTitle>
          <CardDescription>Loading prediction...</CardDescription>
        </CardHeader>
        <CardContent className="flex justify-center items-center py-8">
          <div className="animate-pulse">
            <div className="w-48 h-28 bg-gray-200 dark:bg-gray-700 rounded-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!prediction) {
    return (
      <Card className="col-span-full lg:col-span-1">
        <CardHeader>
          <CardTitle>Current AQI</CardTitle>
          <CardDescription>Unable to load prediction</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-8 text-gray-500">
          <AlertTriangle className="w-12 h-12 mb-2" />
          <p>Failed to fetch current AQI</p>
        </CardContent>
      </Card>
    );
  }

  const { predicted_aqi_index, predicted_calculated_aqi, aqi_category, datetime, generated_at } = prediction;
  const categoryInfo = getAQICategoryInfo(aqi_category);

  return (
    <Card className="col-span-full lg:col-span-1 overflow-hidden">
      <div
        className="h-1"
        style={{ backgroundColor: categoryInfo.color }}
      />
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Wind className="w-5 h-5" />
            Current AQI Prediction
          </CardTitle>
          <AQIBadge category={aqi_category} />
        </div>
        <CardDescription className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          Next hour: {formatDateTime(datetime)}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-col items-center">
        <AQIGauge value={predicted_calculated_aqi} size="lg" />
        
        {/* Both AQI values */}
        <div className="mt-4 w-full grid grid-cols-2 gap-3">
          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">AQI Index</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">
              {predicted_aqi_index.toFixed(2)}
            </p>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-gray-800 rounded-lg text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Calculated AQI</p>
            <p className="text-2xl font-bold" style={{ color: categoryInfo.color }}>
              {predicted_calculated_aqi.toFixed(2)}
            </p>
          </div>
        </div>
        
        <div
          className="mt-4 p-3 rounded-lg text-center w-full"
          style={{ backgroundColor: categoryInfo.bgColor }}
        >
          <p className="text-sm" style={{ color: categoryInfo.textColor }}>
            {categoryInfo.description}
          </p>
        </div>

        <div className="mt-3 text-xs text-gray-400 flex items-center gap-1">
          <CheckCircle2 className="w-3 h-3" />
          Generated at {generated_at}
        </div>
      </CardContent>
    </Card>
  );
}

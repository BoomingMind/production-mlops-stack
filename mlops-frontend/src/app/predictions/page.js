'use client';

import { useState } from 'react';
import { useAQIData } from '@/hooks/useAQIData';
import { AQIChart } from '@/components/aqi';
import { HourlyForecast, DailyForecast } from '@/components/predictions';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { LoadingCard } from '@/components/ui/Loading';
import { RefreshCw, Calendar, Clock, BarChart3, AlertCircle } from 'lucide-react';

export default function PredictionsPage() {
  const [hours, setHours] = useState(48);
  const [days, setDays] = useState(7);
  
  const { hourly, daily, fullPredictions, isLoading, error, refetch } = useAQIData({
    hours,
    days,
    autoRefresh: false,
  });

  const hourOptions = [24, 48, 72, 96, 168];
  const dayOptions = [1, 3, 5, 7];

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Header */}
      <section className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                <BarChart3 className="w-8 h-8 text-blue-600" />
                AQI Predictions
              </h1>
              <p className="text-gray-600 dark:text-gray-400 mt-1">
                Detailed hourly and daily air quality forecasts
              </p>
            </div>
            <Button onClick={refetch} disabled={isLoading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>
      </section>

      <main className="container mx-auto px-4 py-8">
        {/* Error State */}
        {error && (
          <Card className="mb-6 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
            <CardContent className="py-4">
              <div className="flex items-center gap-3 text-red-700 dark:text-red-400">
                <AlertCircle className="w-5 h-5" />
                <p>{error}</p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Controls */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Hourly Range Selector */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Clock className="w-5 h-5" />
                Hourly Forecast Range
              </CardTitle>
              <CardDescription>Select how many hours to forecast</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {hourOptions.map((h) => (
                  <Button
                    key={h}
                    variant={hours === h ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setHours(h)}
                  >
                    {h} hours
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Daily Range Selector */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Calendar className="w-5 h-5" />
                Daily Forecast Range
              </CardTitle>
              <CardDescription>Select how many days to forecast</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {dayOptions.map((d) => (
                  <Button
                    key={d}
                    variant={days === d ? 'primary' : 'outline'}
                    size="sm"
                    onClick={() => setDays(d)}
                  >
                    {d} {d === 1 ? 'day' : 'days'}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {isLoading ? (
          <LoadingCard message="Loading predictions..." />
        ) : (
          <>
            {/* Hourly Forecast */}
            <div className="mb-8">
              <HourlyForecast 
                predictions={hourly?.predictions} 
                isLoading={isLoading}
                maxItems={24}
              />
            </div>

            {/* Chart */}
            <div className="mb-8">
              <AQIChart 
                data={hourly?.predictions}
                title={`${hours}-Hour AQI Forecast`}
                description={`Predicted air quality index for the next ${hours} hours`}
                showThresholds={true}
              />
            </div>

            {/* Daily Forecast */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <DailyForecast 
                dailySummary={daily?.daily_summary} 
                isLoading={isLoading} 
              />

              {/* Statistics */}
              {fullPredictions?.statistics && (
                <Card>
                  <CardHeader>
                    <CardTitle>Forecast Statistics</CardTitle>
                    <CardDescription>
                      Summary for the next {days} days
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {/* AQI Index Statistics */}
                    <div className="mb-6">
                      <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                        AQI Index
                      </h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Average AQI</p>
                          <p className="text-3xl font-bold text-blue-600">
                            {Math.round(fullPredictions.statistics.average_aqi)}
                          </p>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Peak AQI</p>
                          <p className="text-3xl font-bold text-red-600">
                            {Math.round(fullPredictions.statistics.max_aqi)}
                          </p>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Lowest AQI</p>
                          <p className="text-3xl font-bold text-green-600">
                            {Math.round(fullPredictions.statistics.min_aqi)}
                          </p>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Std Deviation</p>
                          <p className="text-3xl font-bold text-gray-600">
                            ±{fullPredictions.statistics.std_deviation.toFixed(1)}
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Calculated AQI Statistics */}
                    <div>
                      <h4 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                        Calculated AQI
                      </h4>
                      <div className="grid grid-cols-2 gap-4">
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Average AQI</p>
                          <p className="text-3xl font-bold text-blue-600">
                            {Math.round(fullPredictions.statistics.calculated_aqi_average)}
                          </p>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Peak AQI</p>
                          <p className="text-3xl font-bold text-red-600">
                            {Math.round(fullPredictions.statistics.calculated_aqi_max)}
                          </p>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Lowest AQI</p>
                          <p className="text-3xl font-bold text-green-600">
                            {Math.round(fullPredictions.statistics.calculated_aqi_min)}
                          </p>
                        </div>
                        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Std Deviation</p>
                          <p className="text-3xl font-bold text-gray-600">
                            ±{fullPredictions.statistics.calculated_aqi_std_deviation.toFixed(1)}
                          </p>
                        </div>
                      </div>
                    </div>
                    
                    {fullPredictions.prediction_info && (
                      <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-500 dark:text-gray-400">
                        <p>Forecast period: {fullPredictions.prediction_info.start_datetime} to {fullPredictions.prediction_info.end_datetime}</p>
                        <p>Generated: {fullPredictions.prediction_info.generated_at}</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </div>
          </>
        )}
      </main>
    </div>
  );
}

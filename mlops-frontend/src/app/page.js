'use client';

import { useAQIData } from '@/hooks/useAQIData';
import { CurrentAQICard, AQIChart, StatsCard } from '@/components/aqi';
import { HourlyForecast, DailyForecast } from '@/components/predictions';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { RefreshCw, AlertCircle, Wind, Droplets, Thermometer, Clock } from 'lucide-react';

export default function Home() {
  const { current, hourly, daily, fullPredictions, isLoading, error, refetch } = useAQIData({
    hours: 48,
    days: 7,
    autoRefresh: true,
    refreshInterval: 300000, // 5 minutes
  });

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 text-white">
        <div className="container mx-auto px-4 py-12">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-8">
            <div className="text-center lg:text-left">
              <h1 className="text-4xl lg:text-5xl font-bold mb-4">
                Air Quality Prediction
              </h1>
              <p className="text-lg text-blue-100 max-w-xl">
                Real-time AQI predictions powered by machine learning. 
                Get hourly and daily forecasts to plan your activities safely.
              </p>
              <div className="flex flex-wrap gap-4 mt-6 justify-center lg:justify-start">
                <div className="flex items-center gap-2 bg-white/10 rounded-full px-4 py-2">
                  <Clock className="w-4 h-4" />
                  <span className="text-sm">Hourly Updates</span>
                </div>
                <div className="flex items-center gap-2 bg-white/10 rounded-full px-4 py-2">
                  <Wind className="w-4 h-4" />
                  <span className="text-sm">7-Day Forecast</span>
                </div>
                <div className="flex items-center gap-2 bg-white/10 rounded-full px-4 py-2">
                  <Thermometer className="w-4 h-4" />
                  <span className="text-sm">ML Powered</span>
                </div>
              </div>
            </div>
            
            {/* Quick Stats */}
            {current?.success && current.prediction && (
              <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-6 min-w-[280px]">
                <p className="text-sm text-blue-200 mb-2">Current Prediction</p>
                <div className="flex items-end gap-3">
                  <span className="text-6xl font-bold">
                    {Math.round(current.prediction.predicted_aqi_index)}
                  </span>
                  <span className="text-xl text-blue-200 pb-2">AQI</span>
                </div>
                <div className="mt-3 px-3 py-1 bg-white/20 rounded-full inline-block">
                  <span className="text-sm font-medium">
                    {current.prediction.aqi_category}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Error State */}
        {error && (
          <Card className="mb-6 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3 text-red-700 dark:text-red-400">
                  <AlertCircle className="w-5 h-5" />
                  <div>
                    <p className="font-medium">Connection Error</p>
                    <p className="text-sm opacity-80">{error}</p>
                  </div>
                </div>
                <Button onClick={refetch} variant="outline" size="sm">
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Refresh Button */}
        <div className="flex justify-end mb-6">
          <Button 
            onClick={refetch} 
            variant="outline" 
            size="sm"
            disabled={isLoading}
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            {isLoading ? 'Refreshing...' : 'Refresh Data'}
          </Button>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Current AQI Card */}
          <CurrentAQICard 
            prediction={current?.prediction} 
            isLoading={isLoading} 
          />

          {/* Stats Card */}
          <StatsCard 
            stats={fullPredictions?.statistics} 
            isLoading={isLoading} 
          />

          {/* Daily Forecast */}
          <DailyForecast 
            dailySummary={daily?.daily_summary} 
            isLoading={isLoading} 
          />
        </div>

        {/* Hourly Forecast */}
        <div className="mt-6">
          <HourlyForecast 
            predictions={hourly?.predictions} 
            isLoading={isLoading}
            maxItems={16}
          />
        </div>

        {/* Chart */}
        <div className="mt-6">
          <AQIChart 
            data={hourly?.predictions?.slice(0, 48)}
            title="48-Hour AQI Forecast"
            description="Predicted air quality index for the next 48 hours"
            showThresholds={true}
          />
        </div>

        {/* AQI Information Cards */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            Understanding AQI Levels
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {[
              { range: '0-50', category: 'Good', color: '#00e400', advice: 'Air quality is satisfactory' },
              { range: '51-100', category: 'Moderate', color: '#ffff00', advice: 'Acceptable air quality' },
              { range: '101-150', category: 'Unhealthy (SG)', color: '#ff7e00', advice: 'Sensitive groups affected' },
              { range: '151-200', category: 'Unhealthy', color: '#ff0000', advice: 'Everyone may be affected' },
              { range: '201-300', category: 'Very Unhealthy', color: '#8f3f97', advice: 'Health alert' },
              { range: '301+', category: 'Hazardous', color: '#7e0023', advice: 'Emergency conditions' },
            ].map((level) => (
              <Card key={level.category} className="overflow-hidden">
                <div 
                  className="h-2" 
                  style={{ backgroundColor: level.color }}
                />
                <CardContent className="p-4">
                  <p className="text-sm font-semibold text-gray-900 dark:text-white">
                    {level.range}
                  </p>
                  <p 
                    className="text-xs font-medium mt-1"
                    style={{ color: level.color }}
                  >
                    {level.category}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                    {level.advice}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

'use client';

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
} from 'recharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card';
import { getAQIColor } from '@/lib/api';
import { formatTime, formatDate } from '@/lib/utils';

// AQI threshold reference lines
const AQI_THRESHOLDS = [
  { value: 50, label: 'Good', color: '#00e400' },
  { value: 100, label: 'Moderate', color: '#ffff00' },
  { value: 150, label: 'Unhealthy (SG)', color: '#ff7e00' },
  { value: 200, label: 'Unhealthy', color: '#ff0000' },
];

// Custom tooltip component
function CustomTooltip({ active, payload, label }) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const calculatedAqi = data.predicted_calculated_aqi;
    const aqiIndex = data.predicted_aqi_index;
    const color = getAQIColor(calculatedAqi);

    return (
      <div className="bg-white dark:bg-gray-800 p-3 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700">
        <p className="text-sm font-medium text-gray-900 dark:text-white">
          {data.datetime}
        </p>
        <div className="flex items-center gap-2 mt-1">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: color }}
          />
          <span className="text-lg font-bold" style={{ color }}>
            AQI: {calculatedAqi.toFixed(1)}
          </span>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
          Index: {aqiIndex.toFixed(2)} • {data.aqi_category}
        </p>
      </div>
    );
  }
  return null;
}

export function AQIChart({ data, title = 'AQI Forecast', description, showThresholds = true }) {
  if (!data || data.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>No data available</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Process data for chart
  const chartData = data.map((item, index) => ({
    ...item,
    index,
    displayTime: formatTime(item.datetime),
    displayDate: formatDate(item.datetime),
  }));

  // Calculate chart domain based on calculated AQI
  const maxAQI = Math.max(...data.map((d) => d.predicted_calculated_aqi));
  const yAxisMax = Math.ceil(maxAQI / 50) * 50 + 50;

  return (
    <Card className="col-span-full">
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description && <CardDescription>{description}</CardDescription>}
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart
              data={chartData}
              margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
            >
              <defs>
                <linearGradient id="aqiGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-gray-200 dark:stroke-gray-700" />
              <XAxis
                dataKey="displayTime"
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                className="text-gray-500"
                interval="preserveStartEnd"
              />
              <YAxis
                domain={[0, yAxisMax]}
                tick={{ fontSize: 12 }}
                tickLine={false}
                axisLine={false}
                className="text-gray-500"
              />
              <Tooltip content={<CustomTooltip />} />
              
              {showThresholds &&
                AQI_THRESHOLDS.map((threshold) => (
                  <ReferenceLine
                    key={threshold.value}
                    y={threshold.value}
                    stroke={threshold.color}
                    strokeDasharray="5 5"
                    strokeOpacity={0.5}
                  />
                ))}

              <Area
                type="monotone"
                dataKey="predicted_calculated_aqi"
                stroke="#3b82f6"
                strokeWidth={2}
                fill="url(#aqiGradient)"
                dot={false}
                activeDot={{
                  r: 6,
                  fill: '#3b82f6',
                  stroke: '#fff',
                  strokeWidth: 2,
                }}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        {showThresholds && (
          <div className="flex flex-wrap gap-4 mt-4 justify-center">
            {AQI_THRESHOLDS.map((threshold) => (
              <div key={threshold.value} className="flex items-center gap-1.5">
                <div
                  className="w-3 h-0.5"
                  style={{ backgroundColor: threshold.color }}
                />
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {threshold.label} ({threshold.value})
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

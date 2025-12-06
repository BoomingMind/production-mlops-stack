'use client';

import { useState, useEffect, useCallback } from 'react';
import {
  getCurrentPrediction,
  getHourlyPredictions,
  getDailyPredictions,
  getPredictions,
  getHealth,
} from '@/lib/api';

/**
 * Hook to fetch all AQI data
 */
export function useAQIData(options = {}) {
  const { hours = 24, days = 7, autoRefresh = true, refreshInterval = 300000 } = options;

  const [data, setData] = useState({
    current: null,
    hourly: null,
    daily: null,
    fullPredictions: null,
    health: null,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    try {
      setError(null);

      const [currentRes, hourlyRes, dailyRes, fullRes, healthRes] = await Promise.allSettled([
        getCurrentPrediction(),
        getHourlyPredictions(hours),
        getDailyPredictions(days),
        getPredictions(days),
        getHealth(),
      ]);

      setData({
        current: currentRes.status === 'fulfilled' ? currentRes.value : null,
        hourly: hourlyRes.status === 'fulfilled' ? hourlyRes.value : null,
        daily: dailyRes.status === 'fulfilled' ? dailyRes.value : null,
        fullPredictions: fullRes.status === 'fulfilled' ? fullRes.value : null,
        health: healthRes.status === 'fulfilled' ? healthRes.value : null,
      });

      // Check if all requests failed
      const allFailed = [currentRes, hourlyRes, dailyRes].every(
        (res) => res.status === 'rejected'
      );

      if (allFailed) {
        setError('Failed to connect to the AQI prediction server');
      }
    } catch (err) {
      setError(err.message || 'Failed to fetch AQI data');
    } finally {
      setIsLoading(false);
    }
  }, [hours, days]);

  useEffect(() => {
    fetchData();

    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(fetchData, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchData, autoRefresh, refreshInterval]);

  return {
    ...data,
    isLoading,
    error,
    refetch: fetchData,
  };
}

/**
 * Hook for current prediction only
 */
export function useCurrentPrediction() {
  const [prediction, setPrediction] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPrediction = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getCurrentPrediction();
      if (response.success) {
        setPrediction(response.prediction);
      } else {
        setError(response.error || 'Failed to fetch prediction');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPrediction();
  }, [fetchPrediction]);

  return { prediction, isLoading, error, refetch: fetchPrediction };
}

/**
 * Hook for hourly predictions
 */
export function useHourlyPredictions(hours = 24) {
  const [predictions, setPredictions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPredictions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getHourlyPredictions(hours);
      if (response.success) {
        setPredictions(response.predictions);
      } else {
        setError(response.error || 'Failed to fetch predictions');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [hours]);

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  return { predictions, isLoading, error, refetch: fetchPredictions };
}

/**
 * Hook for daily predictions
 */
export function useDailyPredictions(days = 7) {
  const [dailySummary, setDailySummary] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPredictions = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await getDailyPredictions(days);
      if (response.success) {
        setDailySummary(response.daily_summary);
      } else {
        setError(response.error || 'Failed to fetch predictions');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [days]);

  useEffect(() => {
    fetchPredictions();
  }, [fetchPredictions]);

  return { dailySummary, isLoading, error, refetch: fetchPredictions };
}

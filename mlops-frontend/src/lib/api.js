const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// AQI color mapping based on EPA standards
export const AQI_COLORS = {
  'Good': '#00e400',
  'Moderate': '#ffff00',
  'Unhealthy for Sensitive Groups': '#ff7e00',
  'Unhealthy': '#ff0000',
  'Very Unhealthy': '#8f3f97',
  'Hazardous': '#7e0023'
};

// AQI category information
export const AQI_CATEGORIES = {
  'Good': {
    color: '#00e400',
    bgColor: '#f0f9ff',
    textColor: '#0369a1',
    description: 'Air quality is satisfactory, and air pollution poses little or no risk.',
    range: '0-50'
  },
  'Moderate': {
    color: '#ffff00',
    bgColor: '#fef3c7',
    textColor: '#92400e',
    description: 'Air quality is acceptable. However, there may be a risk for some people.',
    range: '51-100'
  },
  'Unhealthy for Sensitive Groups': {
    color: '#ff7e00',
    bgColor: '#fed7aa',
    textColor: '#9a3412',
    description: 'Members of sensitive groups may experience health effects.',
    range: '101-150'
  },
  'Unhealthy': {
    color: '#ff0000',
    bgColor: '#fecaca',
    textColor: '#dc2626',
    description: 'Everyone may begin to experience health effects.',
    range: '151-200'
  },
  'Very Unhealthy': {
    color: '#8f3f97',
    bgColor: '#e9d5ff',
    textColor: '#7c3aed',
    description: 'Health alert: everyone may experience more serious health effects.',
    range: '201-300'
  },
  'Hazardous': {
    color: '#7e0023',
    bgColor: '#fee2e2',
    textColor: '#b91c1c',
    description: 'Health warning of emergency conditions. The entire population is more likely to be affected.',
    range: '301+'
  }
};

// Get AQI color based on value
export function getAQIColor(aqi) {
  if (aqi <= 50) return AQI_COLORS['Good'];
  if (aqi <= 100) return AQI_COLORS['Moderate'];
  if (aqi <= 150) return AQI_COLORS['Unhealthy for Sensitive Groups'];
  if (aqi <= 200) return AQI_COLORS['Unhealthy'];
  if (aqi <= 300) return AQI_COLORS['Very Unhealthy'];
  return AQI_COLORS['Hazardous'];
}

// Get AQI category based on value
export function getAQICategory(aqi) {
  if (aqi <= 50) return 'Good';
  if (aqi <= 100) return 'Moderate';
  if (aqi <= 150) return 'Unhealthy for Sensitive Groups';
  if (aqi <= 200) return 'Unhealthy';
  if (aqi <= 300) return 'Very Unhealthy';
  return 'Hazardous';
}

// Get AQI category information
export function getAQICategoryInfo(category) {
  return AQI_CATEGORIES[category] || AQI_CATEGORIES['Good'];
}

// API Functions

// Generic fetch wrapper with error handling
async function apiRequest(endpoint, options = {}) {
  try {
    const url = `${API_BASE_URL}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
}

// Get current AQI prediction
export async function getCurrentPrediction() {
  return apiRequest('/api/predict/current');
}

// Get hourly predictions
export async function getHourlyPredictions(hours = 24) {
  return apiRequest(`/api/predict/hourly?hours=${hours}`);
}

// Get daily predictions
export async function getDailyPredictions(days = 7) {
  return apiRequest(`/api/predict/daily?days=${days}`);
}

// Get full predictions (multi-day)
export async function getPredictions(days = 7) {
  return apiRequest(`/api/predict?days=${days}`);
}

// RAG API functions

// Query RAG system
export async function queryRAG(query) {
  return apiRequest('/api/rag/query', {
    method: 'POST',
    body: JSON.stringify({ query }),
  });
}

// Get RAG sources
export async function getRAGSources() {
  return apiRequest('/api/rag/sources');
}

// Get RAG guardrail stats
export async function getRAGGuardrailStats() {
  return apiRequest('/api/rag/guardrails/stats');
}

// Get LLM stats
export async function getLLMStats() {
  return apiRequest('/api/llm/stats');
}

// Health check
export async function getHealth() {
  return apiRequest('/health');
}
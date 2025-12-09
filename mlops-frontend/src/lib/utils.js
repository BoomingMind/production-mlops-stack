// Date and time formatting utilities

// Utility function to combine CSS classes
export function cn(...classes) {
  return classes.filter(Boolean).join(' ');
}

// Format time from datetime string (HH:MM)
export function formatTime(datetimeString) {
  try {
    const date = new Date(datetimeString);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } catch (error) {
    console.error('Error formatting time:', error);
    return datetimeString;
  }
}

// Format date from datetime string (MMM DD)
export function formatDate(datetimeString) {
  try {
    const date = new Date(datetimeString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  } catch (error) {
    console.error('Error formatting date:', error);
    return datetimeString;
  }
}

// Format full date and time
export function formatDateTime(datetimeString) {
  try {
    const date = new Date(datetimeString);
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false
    });
  } catch (error) {
    console.error('Error formatting datetime:', error);
    return datetimeString;
  }
}

// Format relative time (e.g., "2 hours ago")
export function formatRelativeTime(datetimeString) {
  try {
    const date = new Date(datetimeString);
    const now = new Date();
    const diffInMs = now - date;
    const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
    const diffInHours = Math.floor(diffInMinutes / 60);
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInMinutes < 1) return 'Just now';
    if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
    if (diffInHours < 24) return `${diffInHours}h ago`;
    if (diffInDays < 7) return `${diffInDays}d ago`;

    return formatDate(datetimeString);
  } catch (error) {
    console.error('Error formatting relative time:', error);
    return datetimeString;
  }
}

// Number formatting utilities

// Format number with specified decimal places
export function formatNumber(num, decimals = 2) {
  if (typeof num !== 'number' || isNaN(num)) return '0';
  return num.toFixed(decimals);
}

// Format AQI value
export function formatAQI(aqi) {
  if (typeof aqi !== 'number' || isNaN(aqi)) return 'N/A';
  return Math.round(aqi).toString();
}

// Array and object utilities

// Check if array is empty or null
export function isEmpty(arr) {
  return !arr || arr.length === 0;
}

// Get random item from array
export function randomItem(arr) {
  if (isEmpty(arr)) return null;
  return arr[Math.floor(Math.random() * arr.length)];
}

// Debounce function for search inputs
export function debounce(func, wait) {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
}

// Local storage utilities

// Safe localStorage get
export function getFromStorage(key, defaultValue = null) {
  if (typeof window === 'undefined') return defaultValue;
  try {
    const item = window.localStorage.getItem(key);
    return item ? JSON.parse(item) : defaultValue;
  } catch (error) {
    console.error('Error reading from localStorage:', error);
    return defaultValue;
  }
}

// Safe localStorage set
export function setToStorage(key, value) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch (error) {
    console.error('Error writing to localStorage:', error);
  }
}

// Remove from localStorage
export function removeFromStorage(key) {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.removeItem(key);
  } catch (error) {
    console.error('Error removing from localStorage:', error);
  }
}
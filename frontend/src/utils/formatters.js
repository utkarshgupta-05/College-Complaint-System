/**
 * frontend/src/utils/formatters.js
 * ---------------------------------
 * Robust formatting and data normalization helpers.
 * Prevents TypeError crashes from undefined/null values or malformed API responses.
 */

/**
 * Safely format a number to fixed decimal places.
 * Never throws TypeError; falls back gracefully.
 *
 * @param {any} val - Value to format
 * @param {number} decimals - Number of decimal places (default: 1)
 * @param {string} fallback - Fallback string if value is null, undefined, or NaN
 * @returns {string} Formatted number string
 */
export function formatNumber(val, decimals = 1, fallback = '0.0') {
  if (val === null || val === undefined || val === '') {
    return fallback;
  }
  const num = Number(val);
  if (Number.isNaN(num)) {
    return fallback;
  }
  return num.toFixed(decimals);
}

/**
 * Safely format a ratio or percentage into a display string (e.g., "85.2%").
 * Handles both 0-1 scale (0.852 -> 85.2%) and 0-100 scale (85.2 -> 85.2%).
 *
 * @param {any} val - Number or string to format
 * @param {number} decimals - Number of decimal places
 * @param {string} fallback - Fallback string
 * @returns {string} Formatted percentage
 */
export function formatPercent(val, decimals = 1, fallback = '0.0%') {
  if (val === null || val === undefined || val === '') {
    return fallback;
  }
  const num = Number(val);
  if (Number.isNaN(num)) {
    return fallback;
  }

  // If already on 0-100 scale, don't multiply by 100
  // e.g. 85.2 becomes 85.2%
  // If between 0 and 1, multiply by 100 (e.g. 0.852 -> 85.2%)
  const percentage = (num > 0 && num <= 1) ? num * 100 : num;
  return `${percentage.toFixed(decimals)}%`;
}

/**
 * Safely format date string into localized display string.
 *
 * @param {any} dateVal - Date input (string, number, or Date)
 * @param {string} fallback - Fallback string
 * @returns {string}
 */
export function formatDate(dateVal, fallback = '—') {
  if (!dateVal) return fallback;
  try {
    const d = new Date(dateVal);
    if (Number.isNaN(d.getTime())) return fallback;
    return d.toLocaleString();
  } catch {
    return fallback;
  }
}

/**
 * Guarantees that the returned value is a safe Array.
 *
 * @param {any} arr
 * @returns {Array}
 */
export function safeArray(arr) {
  return Array.isArray(arr) ? arr : [];
}

/**
 * Guarantees that the returned value is a safe Object.
 *
 * @param {any} obj
 * @returns {object}
 */
export function safeObject(obj) {
  if (obj && typeof obj === 'object' && !Array.isArray(obj)) {
    return obj;
  }
  return {};
}

/**
 * Safely extract string with fallback.
 *
 * @param {any} val
 * @param {string} fallback
 * @returns {string}
 */
export function safeString(val, fallback = '—') {
  if (val === null || val === undefined) return fallback;
  const s = String(val).trim();
  return s.length > 0 ? s : fallback;
}

/**
 * Normalize priority string to standard lowercase key (low, medium, high, critical).
 *
 * @param {string} prio
 * @returns {'low'|'medium'|'high'|'critical'}
 */
export function normalizePriority(prio) {
  if (!prio) return 'medium';
  const clean = String(prio).toLowerCase().trim();
  if (clean === 'critical') return 'critical';
  if (clean === 'high') return 'high';
  if (clean === 'low') return 'low';
  return 'medium';
}

/**
 * Normalize status string to standard lowercase key.
 *
 * @param {string} status
 * @returns {string}
 */
export function normalizeStatus(status) {
  if (!status) return 'submitted';
  return String(status).toLowerCase().trim();
}


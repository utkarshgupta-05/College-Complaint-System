/**
 * frontend/src/api.js
 * -------------------
 * API client module for communication with FastAPI backend.
 */

const API_BASE = '/api';

export const getStoredToken = () => localStorage.getItem('complaint_auth_token');
export const setStoredToken = (token) => localStorage.setItem('complaint_auth_token', token);
export const clearStoredToken = () => localStorage.removeItem('complaint_auth_token');

export const getStoredUser = () => {
  const userStr = localStorage.getItem('complaint_auth_user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

export const setStoredUser = (user) => {
  localStorage.setItem('complaint_auth_user', JSON.stringify(user));
};

export async function apiRequest(endpoint, options = {}) {
  const token = getStoredToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || JSON.stringify(errorJson);
    } catch {
      errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

// Auth API
export const apiLogin = async (username, password) => {
  const data = await apiRequest('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
  setStoredToken(data.access_token);
  setStoredUser(data.user);
  return data;
};

export const apiGetMe = async () => apiRequest('/auth/me');

// Complaint API
export const apiAnalyzeComplaint = async (text, location, options = {}) => {
  return apiRequest('/complaints/analyze', {
    method: 'POST',
    body: JSON.stringify({ complaint_text: text, location: location || null }),
    ...options,
  });
};

export const apiSubmitComplaint = async (text, location, student_dept, options = {}) => {
  return apiRequest('/complaints', {
    method: 'POST',
    body: JSON.stringify({
      complaint_text: text,
      location: location || null,
      student_dept: student_dept || null,
    }),
    ...options,
  });
};

export const apiListComplaints = async (filters = {}, options = {}) => {
  const params = new URLSearchParams();
  if (filters.status) params.append('status', filters.status);
  if (filters.category) params.append('category', filters.category);
  if (filters.priority) params.append('priority', String(filters.priority).toUpperCase());
  if (filters.needs_review !== undefined && filters.needs_review !== null) {
    params.append('needs_review', filters.needs_review);
  }
  const queryString = params.toString() ? `?${params.toString()}` : '';
  return apiRequest(`/complaints${queryString}`, options);
};

export const apiGetComplaintDetail = async (id, options = {}) => {
  return apiRequest(`/complaints/${id}`, options);
};

export const apiUpdateComplaintStatus = async (id, status, options = {}) => {
  return apiRequest(`/complaints/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status: String(status).toLowerCase() }),
    ...options,
  });
};

export const apiOverridePriority = async (id, override_priority, reason, options = {}) => {
  return apiRequest(`/complaints/${id}/priority-override`, {
    method: 'POST',
    body: JSON.stringify({
      override_priority: String(override_priority).toUpperCase(),
      reason: String(reason).trim(),
    }),
    ...options,
  });
};

export const apiOverrideCategory = async (id, override_category, reason, options = {}) => {
  return apiRequest(`/complaints/${id}/category-override`, {
    method: 'POST',
    body: JSON.stringify({
      override_category: String(override_category),
      reason: String(reason || 'Staff category review').trim(),
    }),
    ...options,
  });
};


// Analytics API
export const apiGetAnalyticsOverview = async (options = {}) => {
  return apiRequest('/analytics/overview', options);
};

export const apiGetRecurringClusters = async (options = {}) => {
  return apiRequest('/analytics/clusters', options);
};

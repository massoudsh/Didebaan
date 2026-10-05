const BASE = import.meta.env.VITE_API_BASE || '';
const TOKEN_KEY = 'didebaan.token';
const USER_KEY = 'didebaan.user';

let onUnauthorized = () => {};

export const auth = {
  get token() {
    return localStorage.getItem(TOKEN_KEY);
  },
  get user() {
    return localStorage.getItem(USER_KEY) || '';
  },
  set(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, user);
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
  onUnauthorized(fn) {
    onUnauthorized = fn;
  },
};

export class ApiError extends Error {
  constructor(status, data) {
    super(extractMessage(status, data));
    this.status = status;
    this.data = data;
  }
}

function extractMessage(status, data) {
  if (status === 429) return 'تعداد درخواست‌ها از حد مجاز گذشته است؛ کمی بعد دوباره تلاش کنید.';
  if (!data) return `خطای سرور (${status})`;
  if (typeof data === 'string') return data;
  if (data.detail) return data.detail;
  if (data.error) return data.error;
  const first = Object.entries(data)[0];
  if (first) {
    const [field, value] = first;
    const text = Array.isArray(value) ? value.join('، ') : String(value);
    return field === 'non_field_errors' ? text : `${field}: ${text}`;
  }
  return `خطای سرور (${status})`;
}

function buildUrl(path, params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) query.set(key, value);
  });
  const qs = query.toString();
  return `${BASE}${path}${qs ? `?${qs}` : ''}`;
}

async function send(path, { method = 'GET', body, params } = {}) {
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (auth.token) headers.Authorization = `Token ${auth.token}`;

  const response = await fetch(buildUrl(path, params), {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });

  if (response.status === 401 && auth.token) {
    auth.clear();
    onUnauthorized();
  }
  return response;
}

async function request(path, options) {
  const response = await send(path, options);
  const text = await response.text();
  let data = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  if (!response.ok) throw new ApiError(response.status, data);
  return data;
}

export async function download(path, params, fallbackName) {
  const response = await send(path, { params });
  if (!response.ok) {
    let data = null;
    try {
      data = await response.json();
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(response.status, data);
  }
  const disposition = response.headers.get('Content-Disposition') || '';
  const match = disposition.match(/filename="([^"]+)"/);
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = match ? match[1] : fallbackName;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export async function login(username, password) {
  const data = await request('/api/auth/token/', { method: 'POST', body: { username, password } });
  auth.set(data.token, username);
  return data;
}

export const api = {
  alerts: (params) => request('/api/alerts/', { params }),
  alert: (alertId) => request(`/api/alerts/${encodeURIComponent(alertId)}/`),
  statistics: (days = 30) => request('/api/alerts/statistics/', { params: { days } }),
  openCount: () => request('/api/alerts/open_count/'),
  customerCount: (level) =>
    request('/api/customers/', { params: { current_risk_level: level } }).then((d) => d.count),
  comments: (alertId) => request(`/api/alerts/${encodeURIComponent(alertId)}/comments/`),
  addComment: (alertId, comment) =>
    request(`/api/alerts/${encodeURIComponent(alertId)}/comments/`, { method: 'POST', body: { comment } }),
  assign: (alertId, assigned_to, notes) =>
    request(`/api/alerts/${encodeURIComponent(alertId)}/assign/`, { method: 'POST', body: { assigned_to, notes } }),
  review: (alertId, status, notes) =>
    request(`/api/alerts/${encodeURIComponent(alertId)}/review/`, { method: 'POST', body: { status, notes } }),
  bulkAssign: (alert_ids, assigned_to, notes) =>
    request('/api/alerts/bulk-assign/', { method: 'POST', body: { alert_ids, assigned_to, notes } }),
  bulkReview: (alert_ids, status, notes) =>
    request('/api/alerts/bulk-review/', { method: 'POST', body: { alert_ids, status, notes } }),
  exportAlerts: (params) => download('/api/alerts/export/', params, 'alerts_export.csv'),
  exportComments: (params) => download('/api/alerts/comments-export/', params, 'alert_comments_export.csv'),
};

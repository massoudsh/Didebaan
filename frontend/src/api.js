const BASE = import.meta.env?.VITE_API_BASE || '';
const TOKEN_KEY = 'didebaan.token';
const USER_KEY = 'didebaan.user';
const ROLES_KEY = 'didebaan.roles';

let onUnauthorized = () => {};

export const auth = {
  get token() {
    return localStorage.getItem(TOKEN_KEY);
  },
  get user() {
    return localStorage.getItem(USER_KEY) || '';
  },
  get roles() {
    return JSON.parse(localStorage.getItem(ROLES_KEY) || '[]');
  },
  set(token, profile) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, profile.username);
    localStorage.setItem(ROLES_KEY, JSON.stringify(profile.roles || []));
  },
  clear() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(ROLES_KEY);
  },
  onUnauthorized(fn) {
    onUnauthorized = fn;
  },
};

export const ERROR_MESSAGES = {
  offline: 'اتصال شبکه برقرار نیست. اتصال را بررسی کنید؛ ورودی‌های شما حفظ شده‌اند.',
  forbidden: 'اجازهٔ انجام این عملیات را ندارید. با سرپرست یا افسر انطباق تماس بگیرید.',
  notFound: 'مورد درخواستی پیدا نشد؛ ممکن است حذف یا بازارجاع شده باشد.',
  server: 'خطای سرور رخ داد. اگر تکرار شد با پشتیبانی تماس بگیرید.',
  throttled: 'تعداد درخواست‌ها از حد مجاز گذشته است؛ کمی بعد دوباره تلاش کنید.',
  validation: 'اطلاعات ارسالی معتبر نیست. خطاهای مشخص‌شده را اصلاح کنید.',
};

export class ApiError extends Error {
  constructor(status, data) {
    super(extractMessage(status, data));
    this.status = status;
    this.data = data;
    this.kind = kindOf(status);
    this.fieldErrors = fieldErrorsOf(data);
  }
}

function kindOf(status) {
  if (status === 0) return 'offline';
  if (status === 400) return 'validation';
  if (status === 401) return 'unauthorized';
  if (status === 403) return 'forbidden';
  if (status === 404) return 'notFound';
  if (status === 429) return 'throttled';
  if (status >= 500) return 'server';
  return 'request';
}

function fieldErrorsOf(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) return {};
  const errors = {};
  Object.entries(data).forEach(([field, value]) => {
    if (field === 'detail' || field === 'error' || field === 'non_field_errors') return;
    errors[field] = Array.isArray(value) ? value.join('، ') : String(value);
  });
  return errors;
}

function extractMessage(status, data) {
  if (status === 429) return ERROR_MESSAGES.throttled;
  if (status === 403) return ERROR_MESSAGES.forbidden;
  if (!data) return status >= 500 ? `${ERROR_MESSAGES.server} (${status})` : `خطای سرور (${status})`;
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

async function send(path, { method = 'GET', body, params, token = auth.token } = {}) {
  const headers = { Accept: 'application/json' };
  if (body !== undefined) headers['Content-Type'] = 'application/json';
  if (token) headers.Authorization = `Token ${token}`;

  let response;
  try {
    response = await fetch(buildUrl(path, params), {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
    });
  } catch (error) {
    if (error && error.name === 'AbortError') throw error;
    throw new ApiError(0, null);
  }

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
  const data = await request('/api/auth/token/', { method: 'POST', body: { username, password }, token: null });
  const profile = await request('/api/auth/me/', { token: data.token });
  auth.set(data.token, profile);
  return profile;
}

export const healthStatus = () => request('/api/health/').then(() => 'online').catch(() => 'offline');

function listed(value) {
  return Array.isArray(value) ? value : (value && value.results) || [];
}

export const api = {
  rules: (params) => request('/api/rules/', { params }),
  updateRule: (ruleId, body) => request(`/api/rules/${encodeURIComponent(ruleId)}/`, { method: 'PATCH', body }),
  simulate: (body) => request('/api/intelligence/simulate/', { method: 'POST', body }),
  screen: (body) => request('/api/intelligence/screen/', { method: 'POST', body }),
  graph: (params) => request('/api/intelligence/graph/', { params }),
  sla: () => request('/api/intelligence/sla/'),
  exportCase: (alert_id) => download('/api/intelligence/case-export/', { alert_id }, 'case-evidence.json'),
  alerts: (params) => request('/api/alerts/', { params }),
  transactions: (params) => request('/api/transactions/', { params }),
  alert: (alertId) => request(`/api/alerts/${encodeURIComponent(alertId)}/`),
  relatedAlerts: (alertId) => request(`/api/alerts/${encodeURIComponent(alertId)}/related/`),
  statistics: (days = 30) => request('/api/alerts/statistics/', { params: { days } }),
  openCount: () => request('/api/alerts/open_count/'),
  customers: (params) => request('/api/customers/', { params }),
  customer: (customerId) => request(`/api/customers/${encodeURIComponent(customerId)}/`),
  customerRiskScores: (customerId) => request(`/api/customers/${encodeURIComponent(customerId)}/risk_scores/`),
  customerAlerts: (customerId) => request(`/api/customers/${encodeURIComponent(customerId)}/alerts/`).then(listed),
  customerTransactions: (customerId) => request(`/api/customers/${encodeURIComponent(customerId)}/transactions/`).then(listed),
  searchDevices: (q) => request('/api/devices/', { params: { search: q } }),
  device: (deviceId) => request(`/api/devices/${encodeURIComponent(deviceId)}/`),
  searchMerchants: (q) => request('/api/merchants/', { params: { search: q } }),
  merchant: (merchantId) => request(`/api/merchants/${encodeURIComponent(merchantId)}/`),
  watchlist: (params) => request('/api/watchlist/', { params }),
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

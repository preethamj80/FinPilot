/**
 * FinPilot Central API Client
 * Manages HTTP requests with session cookie credentials and CSRF tokens.
 */

let csrfToken = null;

export function setCsrfToken(token) {
  csrfToken = token;
}

export function getCsrfToken() {
  return csrfToken;
}

async function request(url, options = {}) {
  const headers = {
    'Accept': 'application/json',
    ...(options.headers || {}),
  };

  // Attach CSRF token on mutating methods
  const method = (options.method || 'GET').toUpperCase();
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method) && csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }

  // If body is JSON, add content-type
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers,
    credentials: 'include', // Ensures finpilot_session cookie is sent
  };

  const response = await fetch(url, config);

  // If 401 Unauthorized, dispatch event for auth context
  if (response.status === 401 && !url.includes('/api/auth/login') && !url.includes('/api/auth/register')) {
    window.dispatchEvent(new CustomEvent('finpilot:unauthorized'));
  }

  if (!response.ok) {
    let errorDetail = '';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || '';
      if (Array.isArray(errorDetail)) {
        errorDetail = errorDetail.map((e) => e.msg || e).join(', ');
      }
    } catch {
      errorDetail = response.statusText || '';
    }

    if (!errorDetail || errorDetail === 'Internal Server Error' || errorDetail === 'Request failed') {
      if (response.status === 500 || response.status === 502 || response.status === 504) {
        errorDetail = 'Backend server is not running or unreachable. Please start the backend with .\\start_backend.ps1';
      } else {
        errorDetail = `Request failed with status ${response.status}`;
      }
    }

    const error = new Error(errorDetail);
    error.status = response.status;
    throw error;
  }

  // Handle empty bodies (204 or DELETE)
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    return response.json();
  }
  return response.text();
}

export const api = {
  get: (url, options) => request(url, { ...options, method: 'GET' }),
  post: (url, body, options) => request(url, { ...options, method: 'POST', body: JSON.stringify(body) }),
  put: (url, body, options) => request(url, { ...options, method: 'PUT', body: JSON.stringify(body) }),
  patch: (url, body, options) => request(url, { ...options, method: 'PATCH', body: JSON.stringify(body) }),
  delete: (url, options) => request(url, { ...options, method: 'DELETE' }),
  upload: (url, formData, options) => request(url, { ...options, method: 'POST', body: formData }),
};

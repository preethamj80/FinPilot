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

function formatErrorDetail(detail) {
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item === 'string' ? item : item?.msg || JSON.stringify(item)))
      .filter(Boolean)
      .join(', ');
  }
  if (detail && typeof detail === 'object') return JSON.stringify(detail);
  return typeof detail === 'string' ? detail.trim() : '';
}

function httpErrorMessage(status, detail, url) {
  const authEndpoint = url.includes('/api/auth/login') || url.includes('/api/auth/register');
  const suffix = detail ? `: ${detail}` : '';

  switch (status) {
    case 400:
      return `Invalid request (400)${suffix}`;
    case 401:
      if (authEndpoint && detail) return detail;
      return detail ? `Authentication required (401): ${detail}` : 'Your session has expired. Please sign in again.';
    case 403:
      return detail
        ? `Request blocked by CSRF or Origin protection (403): ${detail}`
        : 'Request blocked by CSRF or Origin protection (403). Refresh the page and try again.';
    case 500:
      return detail
        ? `Server error (500): ${detail}`
        : 'The server encountered an internal error (500). Please try again later.';
    case 502:
      return detail
        ? `Upstream service error (502): ${detail}`
        : 'The server received an invalid response from an upstream service (502).';
    case 504:
      return detail
        ? `Upstream request timed out (504): ${detail}`
        : 'The server timed out while waiting for an upstream service (504).';
    default:
      return detail || `Request failed with status ${status}`;
  }
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

  let response;
  try {
    response = await fetch(url, config);
  } catch (cause) {
    const error = new Error(
      cause?.name === 'AbortError'
        ? 'The request was cancelled.'
        : 'Could not connect to the FinPilot API. Check your connection and try again.',
      { cause }
    );
    error.status = null;
    error.code = cause?.name === 'AbortError' ? 'REQUEST_ABORTED' : 'NETWORK_ERROR';
    throw error;
  }

  // If 401 Unauthorized, dispatch event for auth context
  if (response.status === 401 && !url.includes('/api/auth/login') && !url.includes('/api/auth/register')) {
    window.dispatchEvent(new CustomEvent('finpilot:unauthorized'));
  }

  if (!response.ok) {
    let errorDetail = '';
    try {
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const errJson = await response.json();
        errorDetail = formatErrorDetail(errJson.detail ?? errJson.message);
      } else {
        errorDetail = (await response.text()).trim();
      }
    } catch {
      errorDetail = '';
    }

    const error = new Error(httpErrorMessage(response.status, errorDetail, url));
    error.status = response.status;
    error.code = `HTTP_${response.status}`;
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

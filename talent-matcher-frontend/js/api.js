// API client
// ============================================================

async function apiFetch(path, options = {}) {
  const hasFormData = options.body instanceof FormData;
  const headers = hasFormData ? {} : { "Content-Type": "application/json" };
  const authHeader = state.authToken && !options.headers?.Authorization
    ? { Authorization: `Bearer ${state.authToken}` }
    : {};

  const response = await fetch(`${state.apiBase}${path}`, {
    ...options,
    headers: {
      ...headers,
      ...authHeader,
      ...(options.headers || {})
    }
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(message || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

// ============================================================


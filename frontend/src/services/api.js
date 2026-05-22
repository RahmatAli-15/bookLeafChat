const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}, timeoutMs = 30000) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
      signal: controller.signal
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }

    return response.json();
  } finally {
    clearTimeout(timer);
  }
}

export function sendChatQuery(payload) {
  return request("/api/chat", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getAnalyticsOverview() {
  return request("/api/analytics/overview");
}

export function getRecentQueries(limit = 20) {
  return request(`/api/analytics/recent-queries?limit=${limit}`);
}

export function getEscalations(limit = 30) {
  return request(`/api/escalations?limit=${limit}`);
}

export function getIdentityAmbiguityQueue(limit = 30) {
  return request(`/api/identity/ambiguity-queue?limit=${limit}`);
}

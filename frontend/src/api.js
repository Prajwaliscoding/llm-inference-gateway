const API_URL = import.meta.env.VITE_API_URL;

async function request(path, apiKey, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
      ...options.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export function signup(email) {
  return request("/auth/signup", null, {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function fetchStats(apiKey, range) {
  return request(`/dashboard/stats?range=${range}`, apiKey);
}

export function fetchHistory(apiKey) {
  return request("/dashboard/history?limit=20", apiKey);
}

export function sendChatCompletion(apiKey, payload) {
  return request("/v1/chat/completions", apiKey, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
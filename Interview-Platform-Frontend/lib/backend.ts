const DEFAULT_BACKEND_URL = "http://127.0.0.1:8000";

export function getBackendUrl() {
  return (process.env.BACKEND_API_URL || DEFAULT_BACKEND_URL).replace(/\/$/, "");
}

export async function proxyJsonRequest(path: string, init?: RequestInit) {
  return fetch(`${getBackendUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    },
    cache: "no-store"
  });
}

// Thin API client. In dev, Vite proxies /api → http://localhost:8000.
// In prod, set VITE_API_BASE to your backend URL.

const BASE = import.meta.env.VITE_API_BASE || "/api";

async function handle(res) {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json();
}

export function health() {
  return fetch(`${BASE}/health`).then(handle);
}

export function analyze(vehicles, floorplanApr = 0.085) {
  return fetch(`${BASE}/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ vehicles, floorplan_apr: floorplanApr }),
  }).then(handle);
}

export function trackCsv(file, daysSinceLastCheck = 7) {
  const form = new FormData();
  form.append("file", file);
  form.append("days_since_last_check", String(daysSinceLastCheck));
  return fetch(`${BASE}/track/csv`, { method: "POST", body: form }).then(handle);
}

export function analyzeCsv(file, floorplanApr = 0.085) {
  const form = new FormData();
  form.append("file", file);
  form.append("floorplan_apr", String(floorplanApr));
  return fetch(`${BASE}/analyze/csv`, { method: "POST", body: form }).then(handle);
}

const BASE = import.meta.env.VITE_API ?? "http://localhost:8000";

async function get(path) {
  const r = await fetch(`${BASE}${path}`);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

export const api = {
  headline:   () => get("/api/headline"),
  specCurve:  () => get("/api/spec-curve"),
  placebo:    () => get("/api/placebo-intime"),
  eventStudy: () => get("/api/event-study"),
  loo:        () => get("/api/leave-one-out"),
};
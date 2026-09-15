const BASE_URL = "http://localhost:8000";

async function request(method, path, body = null) {
  const options = {
    method,
    headers: { "Content-Type": "application/json" },
  };
  if (body !== null) {
    options.body = JSON.stringify(body);
  }
  const response = await fetch(`${BASE_URL}${path}`, options);
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

export const api = {
  getHealth: () => request("GET", "/api/health"),
  getInvestigations: () => request("GET", "/api/investigations"),
  getInvestigation: (id) => request("GET", `/api/investigations/${id}`),
  runInvestigation: (script) =>
    request("POST", "/api/investigations", { script }),
};
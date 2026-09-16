import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";

// Simulated second endpoint — represents an Ubuntu agent.
// In a production deployment this would be a real remote agent
// reporting back to the central management API.
const SIMULATED_ENDPOINTS = [
  {
    id: "local",
    hostname: "local machine",
    platform: "Windows",
    status: "online",
    note: "Active — running investigations via local API",
  },
  {
    id: "ubuntu-sim",
    hostname: "ubuntu-agent-01",
    platform: "Ubuntu 22.04",
    status: "simulated",
    note: "Simulated — same JOCKY script runs unmodified on Linux via psutil",
  },
];

function StatusDot({ status }) {
  const color = status === "online" ? "var(--green)" : status === "simulated" ? "var(--amber)" : "var(--red)";
  return (
    <span style={{
      display: "inline-block", width: 8, height: 8,
      borderRadius: "50%", background: color, marginRight: 6,
    }} />
  );
}

export default function Overview() {
  const [investigations, setInvestigations] = useState([]);
  const [health,         setHealth]         = useState(null);
  const [loading,        setLoading]        = useState(true);

  useEffect(() => {
    Promise.all([api.getInvestigations(), api.getHealth()])
      .then(([invs, h]) => { setInvestigations(invs); setHealth(h); })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading…</div>;

  const totalFindings = investigations.reduce((s, i) => s + i.findings_count, 0);
  const recent = investigations.slice(0, 5);

  return (
    <div>
      <h1 className="page-title">Overview</h1>

      {/* Stats */}
      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">API Status</div>
          <div style={{ paddingTop: 6 }}>
            <span className={`badge ${health ? "badge-green" : "badge-red"}`}>
              {health ? "Online" : "Offline"}
            </span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Investigations</div>
          <div className="stat-value">{investigations.length}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Total Findings</div>
          <div className="stat-value">{totalFindings}</div>
        </div>
      </div>

      {/* Endpoints */}
      <div className="section-label">Managed Endpoints</div>
      <div className="table-wrap" style={{ marginBottom: 32 }}>
        <table>
          <thead>
            <tr><th>Hostname</th><th>Platform</th><th>Status</th><th>Note</th></tr>
          </thead>
          <tbody>
            {SIMULATED_ENDPOINTS.map((ep) => (
              <tr key={ep.id}>
                <td style={{ fontFamily: "monospace", fontSize: 13 }}>{ep.hostname}</td>
                <td>{ep.platform}</td>
                <td>
                  <StatusDot status={ep.status} />
                  <span style={{ fontSize: 12, color: "var(--text-muted)", textTransform: "capitalize" }}>
                    {ep.status}
                  </span>
                </td>
                <td style={{ fontSize: 12, color: "var(--text-muted)" }}>{ep.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Recent investigations */}
      <div className="section-label">Recent Investigations</div>
      {recent.length === 0 ? (
        <div className="card">
          <div className="empty">
            No investigations yet.{" "}
            <Link to="/investigations/new" className="plain-link">Run your first one →</Link>
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Name</th><th>Endpoint</th><th>Findings</th><th>Date</th><th></th></tr>
            </thead>
            <tbody>
              {recent.map((inv) => (
                <tr key={inv.id}>
                  <td>{inv.investigation_name}</td>
                  <td style={{ color: "var(--text-muted)" }}>{inv.endpoint_hostname}</td>
                  <td>
                    <span className={`badge ${inv.findings_count > 0 ? "badge-amber" : "badge-green"}`}>
                      {inv.findings_count} finding{inv.findings_count !== 1 ? "s" : ""}
                    </span>
                  </td>
                  <td style={{ color: "var(--text-muted)" }}>{new Date(inv.started_at).toLocaleString()}</td>
                  <td><Link to={`/investigations/${inv.id}`} className="plain-link">View →</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
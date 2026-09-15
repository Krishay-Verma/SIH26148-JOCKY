import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../api/client";

export default function Investigations() {
  const [investigations, setInvestigations] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.getInvestigations()
      .then(setInvestigations)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading…</div>;

  return (
    <div>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 28 }}>
        <h1 className="page-title" style={{ marginBottom: 0 }}>Investigations</h1>
        <Link to="/investigations/new" className="btn btn-primary">+ New</Link>
      </div>

      {investigations.length === 0 ? (
        <div className="card">
          <div className="empty">
            No investigations yet. <Link to="/investigations/new" className="plain-link">Run your first one →</Link>
          </div>
        </div>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th><th>Name</th><th>Endpoint</th>
                <th>Findings</th><th>Started</th><th>Duration</th>
              </tr>
            </thead>
            <tbody>
              {investigations.map((inv) => {
                const secs = ((new Date(inv.finished_at) - new Date(inv.started_at)) / 1000).toFixed(1);
                return (
                  <tr key={inv.id} className="row-link" onClick={() => navigate(`/investigations/${inv.id}`)}>
                    <td style={{ color: "var(--text-subtle)" }}>{inv.id}</td>
                    <td>{inv.investigation_name}</td>
                    <td style={{ color: "var(--text-muted)" }}>{inv.endpoint_hostname}</td>
                    <td>
                      <span className={`badge ${inv.findings_count > 0 ? "badge-amber" : "badge-green"}`}>
                        {inv.findings_count}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-muted)" }}>{new Date(inv.started_at).toLocaleString()}</td>
                    <td style={{ color: "var(--text-muted)" }}>{secs}s</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
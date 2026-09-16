import { useState, useEffect } from "react";
import { useParams, Link } from "react-router-dom";
import { api } from "../api/client";

// ─── Small helper components ────────────────────────────────────────────────

function SeverityBadge({ severity }) {
  if (severity === "review_recommended") return <span className="badge badge-amber">Review Recommended</span>;
  return <span className="badge badge-gray">Informational</span>;
}

function StatusBadge({ status }) {
  return <span className={`badge ${status === "success" ? "badge-green" : "badge-red"}`}>{status}</span>;
}

// ─── Per-collector evidence tables ──────────────────────────────────────────

function SystemInfoEvidence({ data }) {
  const rows = [
    ["Hostname",     data.hostname],
    ["OS",           data.os],
    ["OS Version",   data.os_version],
    ["Architecture", data.architecture],
    ["CPU Count",    data.cpu_count],
    ["Total Memory", data.total_memory_bytes
      ? `${(data.total_memory_bytes / 1073741824).toFixed(2)} GB`
      : "—"],
    ["Current User", data.current_user],
    ["Collected At", data.collected_at],
  ];
  return (
    <div className="card" style={{ marginBottom: 24 }}>
      <div className="meta-grid">
        {rows.map(([label, val]) => (
          <div className="meta-item" key={label}>
            <label>{label}</label>
            <span>{String(val ?? "—")}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProcessesEvidence({ data }) {
  const procs = data.processes ?? [];
  return (
    <div className="table-wrap" style={{ marginBottom: 24 }}>
      <table>
        <thead>
          <tr><th>PID</th><th>Name</th><th>User</th><th>Exe Path</th></tr>
        </thead>
        <tbody>
          {procs.slice(0, 60).map((p, i) => (
            <tr key={i}>
              <td>{p.pid}</td>
              <td>{p.name}</td>
              <td style={{ color: "var(--text-muted)" }}>{p.username ?? "—"}</td>
              <td style={{ color: "var(--text-muted)", fontFamily: "monospace", fontSize: 12 }}>
                {p.exe_path ?? "—"}
              </td>
            </tr>
          ))}
          {procs.length > 60 && (
            <tr>
              <td colSpan={4} style={{ color: "var(--text-muted)", textAlign: "center" }}>
                +{procs.length - 60} more (showing first 60)
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}

function NetworkEvidence({ data }) {
  const conns = data.connections ?? [];
  if (data.error) {
    return <div className="msg msg-error" style={{ marginBottom: 24 }}>{data.error}</div>;
  }
  return (
    <div className="table-wrap" style={{ marginBottom: 24 }}>
      <table>
        <thead>
          <tr><th>Local</th><th>Remote</th><th>Status</th><th>PID</th></tr>
        </thead>
        <tbody>
          {conns.length === 0
            ? <tr><td colSpan={4} style={{ textAlign: "center", color: "var(--text-muted)" }}>No connections</td></tr>
            : conns.map((c, i) => (
              <tr key={i}>
                <td style={{ fontFamily: "monospace", fontSize: 12 }}>{c.local_address ?? "—"}</td>
                <td style={{ fontFamily: "monospace", fontSize: 12 }}>{c.remote_address ?? "—"}</td>
                <td><span className="badge badge-gray">{c.status}</span></td>
                <td>{c.pid ?? "—"}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

function LoggedInUsersEvidence({ data }) {
  const sessions = data.sessions ?? [];
  return (
    <div className="table-wrap" style={{ marginBottom: 24 }}>
      <table>
        <thead>
          <tr><th>User</th><th>Terminal</th><th>Host</th><th>Login Time</th></tr>
        </thead>
        <tbody>
          {sessions.length === 0
            ? <tr><td colSpan={4} style={{ textAlign: "center", color: "var(--text-muted)" }}>No sessions</td></tr>
            : sessions.map((s, i) => (
              <tr key={i}>
                <td>{s.username}</td>
                <td>{s.terminal ?? "—"}</td>
                <td>{s.host ?? "—"}</td>
                <td style={{ color: "var(--text-muted)" }}>{s.login_time}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

function FileHashEvidence({ data }) {
  const files = data.files ?? [];
  if (data.error) {
    return <div className="msg msg-error" style={{ marginBottom: 24 }}>{data.error}</div>;
  }
  return (
    <div className="table-wrap" style={{ marginBottom: 24 }}>
      <table>
        <thead>
          <tr><th>File</th><th>Size</th><th>SHA-256</th><th>Modified</th></tr>
        </thead>
        <tbody>
          {files.length === 0
            ? <tr><td colSpan={4} style={{ textAlign: "center", color: "var(--text-muted)" }}>No files</td></tr>
            : files.map((f, i) => (
              <tr key={i}>
                <td style={{ fontFamily: "monospace", fontSize: 12 }}>{f.path}</td>
                <td>{f.size_bytes != null ? `${f.size_bytes} B` : "—"}</td>
                <td style={{ fontFamily: "monospace", fontSize: 11, color: "var(--text-muted)" }}>
                  {f.sha256 ? `${f.sha256.slice(0, 16)}…` : "—"}
                </td>
                <td style={{ color: "var(--text-muted)", fontSize: 12 }}>{f.modified_at ?? "—"}</td>
              </tr>
            ))}
        </tbody>
      </table>
    </div>
  );
}

const EVIDENCE_COMPONENTS = {
  system_info:         SystemInfoEvidence,
  processes:           ProcessesEvidence,
  network_connections: NetworkEvidence,
  logged_in_users:     LoggedInUsersEvidence,
  file_hash:           FileHashEvidence,
};

// ─── Main page ───────────────────────────────────────────────────────────────

export default function InvestigationDetail() {
  const { id } = useParams();
  const [record,  setRecord]  = useState(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState(null);

  useEffect(() => {
    api.getInvestigation(id)
      .then(setRecord)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  function downloadJSON() {
    const blob = new Blob(
      [JSON.stringify(record.report_json, null, 2)],
      { type: "application/json" }
    );
    const url = URL.createObjectURL(blob);
    const a   = document.createElement("a");
    a.href     = url;
    a.download = `jocky_report_${id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (loading) return <div className="loading">Loading…</div>;
  if (error)   return <div className="msg msg-error">{error}</div>;

  const report = record.report_json;

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <Link
          to="/investigations"
          className="plain-link"
          style={{ fontSize: 12, color: "var(--text-muted)" }}
        >
          ← All Investigations
        </Link>
      </div>

      <h1 className="page-title">{report.investigation_name}</h1>

            {/* Metadata */}
      <div className="card meta-grid" style={{ marginBottom: 16 }}>
        <div className="meta-item"><label>Endpoint</label><span>{report.endpoint_hostname}</span></div>
        <div className="meta-item"><label>Findings</label><span>{report.findings.length}</span></div>
        <div className="meta-item"><label>Started</label><span>{new Date(report.started_at).toLocaleString()}</span></div>
        <div className="meta-item"><label>Finished</label><span>{new Date(report.finished_at).toLocaleString()}</span></div>
      </div>

      {/* Download buttons */}
      <div className="actions" style={{ marginBottom: 28 }}>
        <button className="btn btn-ghost" onClick={downloadJSON}>
          ↓ Download JSON
        </button>
        <a
          className="btn btn-ghost"
          href={`http://localhost:8000/api/investigations/${id}/report.html`}
          download={`jocky_report_${id}.html`}
        >
          ↓ Download HTML
        </a>
      </div>

      {/* Collector status */}
      <div className="section-title">Collectors</div>
      <div className="table-wrap" style={{ marginBottom: 28 }}>
        <table>
          <thead>
            <tr><th>Collector</th><th>Status</th><th>Detail</th></tr>
          </thead>
          <tbody>
            {report.collector_results.length === 0
              ? <tr><td colSpan={3} style={{ textAlign: "center", color: "var(--text-muted)" }}>No collectors ran</td></tr>
              : report.collector_results.map((cr, i) => (
                <tr key={i}>
                  <td><code style={{ fontFamily: "monospace" }}>{cr.target}</code></td>
                  <td><StatusBadge status={cr.status} /></td>
                  <td style={{ color: "var(--text-muted)" }}>{cr.status === "error" ? cr.error : "OK"}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Findings */}
      <div className="section-title">
        Findings{" "}
        <span style={{ color: "var(--text-muted)", fontWeight: 400 }}>({report.findings.length})</span>
      </div>
      <div className="table-wrap" style={{ marginBottom: 28 }}>
        <table>
          <thead>
            <tr><th>Rule</th><th>Severity</th><th>Summary</th><th>Reason</th></tr>
          </thead>
          <tbody>
            {report.findings.length === 0
              ? <tr><td colSpan={4} style={{ textAlign: "center", color: "var(--text-muted)" }}>No findings</td></tr>
              : report.findings.map((f, i) => (
                <tr key={i}>
                  <td><code style={{ fontFamily: "monospace", fontSize: 12 }}>{f.rule_name}</code></td>
                  <td><SeverityBadge severity={f.severity} /></td>
                  <td>{f.summary}</td>
                  <td style={{ color: "var(--text-muted)", fontSize: 12 }}>{f.reason}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      {/* Evidence per collector */}
      {report.collector_results
        .filter((cr) => cr.status === "success" && cr.data)
        .map((cr, i) => {
          const EvidenceComponent = EVIDENCE_COMPONENTS[cr.target];
          if (!EvidenceComponent) return null;
          return (
            <div key={i}>
              <div className="section-title">{cr.target} — Evidence</div>
              <EvidenceComponent data={cr.data} />
            </div>
          );
        })}
    </div>
  );
}

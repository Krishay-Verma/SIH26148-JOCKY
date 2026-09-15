import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";

const DEFAULT_SCRIPT = `investigation "Endpoint Triage" {
    collect system_info;
    collect processes;
    collect network_connections;
    collect logged_in_users;
    collect file_hash;
    analyze suspicious_processes;
    analyze missing_paths;
    analyze process_network_correlation;
    report "triage_report";
}`;

export default function NewInvestigation() {
  const [script, setScript] = useState(DEFAULT_SCRIPT);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  async function handleRun() {
    setError(null);
    setRunning(true);
    try {
      const result = await api.runInvestigation(script);
      navigate(`/investigations/${result.id}`);
    } catch (e) {
      setError(e.message);
      setRunning(false);
    }
  }

  return (
    <div>
      <h1 className="page-title">New Investigation</h1>

      {error && <div className="msg msg-error"><strong>Error:</strong> {error}</div>}

      <div className="field">
        <label>JOCKY Script</label>
        <textarea
          className="script-editor"
          value={script}
          onChange={(e) => setScript(e.target.value)}
          rows={14}
          spellCheck={false}
        />
      </div>

      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 16, lineHeight: 1.8 }}>
        <strong>Collectors:</strong> system_info · processes · network_connections · logged_in_users · file_hash<br />
        <strong>Rules:</strong> suspicious_processes · missing_paths · process_network_correlation
      </div>

      <div className="actions">
        <button className="btn btn-primary" onClick={handleRun} disabled={running || !script.trim()}>
          {running ? "Running…" : "▶  Run Investigation"}
        </button>
      </div>
    </div>
  );
}
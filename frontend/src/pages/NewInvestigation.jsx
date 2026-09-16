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

// What a validation success response looks like rendered as a small summary.
function ValidationSuccess({ result }) {
  return (
    <div className="msg msg-success">
      <strong>✓ Script is valid</strong> — investigation{" "}
      <em>"{result.investigation_name}"</em> contains{" "}
      {result.collect_count} collector{result.collect_count !== 1 ? "s" : ""},{" "}
      {result.analyze_count} rule{result.analyze_count !== 1 ? "s" : ""},{" "}
      {result.has_report ? "and a report command." : "no report command."}
    </div>
  );
}

export default function NewInvestigation() {
  const [script,       setScript]       = useState(DEFAULT_SCRIPT);
  const [running,      setRunning]      = useState(false);
  const [validating,   setValidating]   = useState(false);
  const [error,        setError]        = useState(null);
  const [validation,   setValidation]   = useState(null); // null | { valid, ... }
  const navigate = useNavigate();

  // Clear validation feedback whenever the user edits the script.
  function handleScriptChange(e) {
    setScript(e.target.value);
    setValidation(null);
    setError(null);
  }

  async function handleValidate() {
    setError(null);
    setValidation(null);
    setValidating(true);
    try {
      const result = await api.validateScript(script);
      setValidation(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setValidating(false);
    }
  }

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

      {error      && <div className="msg msg-error"><strong>Error:</strong> {error}</div>}
      {validation && <ValidationSuccess result={validation} />}

      <div className="field">
        <label>JOCKY Script</label>
        <textarea
          className="script-editor"
          value={script}
          onChange={handleScriptChange}
          rows={14}
          spellCheck={false}
        />
      </div>

      <div style={{ fontSize: 12, color: "var(--text-muted)", marginBottom: 16, lineHeight: 1.8 }}>
        <strong>Collectors:</strong> system_info · processes · network_connections · logged_in_users · file_hash<br />
        <strong>Rules:</strong> suspicious_processes · missing_paths · process_network_correlation
      </div>

      <div className="actions">
        <button
          className="btn btn-ghost"
          onClick={handleValidate}
          disabled={validating || running || !script.trim()}
        >
          {validating ? "Validating…" : "✓  Validate"}
        </button>
        <button
          className="btn btn-primary"
          onClick={handleRun}
          disabled={running || validating || !script.trim()}
        >
          {running ? "Running…" : "▶  Run Investigation"}
        </button>
      </div>
    </div>
  );
}
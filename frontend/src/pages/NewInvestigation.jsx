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

function CompiledIR({ result }) {
  return (
    <div className="card" style={{ marginBottom: 16 }}>
      <div className="section-label">Compiled IR — {result.token_count} tokens → {result.command_count} commands</div>
      <table style={{ width: "100%", borderCollapse: "collapse", marginBottom: 12 }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", padding: "6px 8px", fontSize: 11, color: "var(--text-subtle)", textTransform: "uppercase" }}>#</th>
            <th style={{ textAlign: "left", padding: "6px 8px", fontSize: 11, color: "var(--text-subtle)", textTransform: "uppercase" }}>Type</th>
            <th style={{ textAlign: "left", padding: "6px 8px", fontSize: 11, color: "var(--text-subtle)", textTransform: "uppercase" }}>Target</th>
          </tr>
        </thead>
        <tbody>
          {result.commands.map((cmd, i) => (
            <tr key={i} style={{ borderTop: "1px solid var(--border)" }}>
              <td style={{ padding: "6px 8px", color: "var(--text-subtle)", fontSize: 12 }}>{i}</td>
              <td style={{ padding: "6px 8px", fontFamily: "monospace", fontSize: 12 }}>{cmd.type}</td>
              <td style={{ padding: "6px 8px", fontFamily: "monospace", fontSize: 12, color: "var(--text-muted)" }}>{cmd.target}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div style={{ fontSize: 11, color: "var(--text-subtle)", marginBottom: 4 }}>IR (base64-encoded)</div>
      <div style={{
        fontFamily: "monospace", fontSize: 11, background: "#1a1a1a", color: "#aaa",
        padding: "8px 12px", borderRadius: 6, wordBreak: "break-all", lineHeight: 1.6
      }}>
        {result.ir_base64}
      </div>
    </div>
  );
}

export default function NewInvestigation() {
  const [script,     setScript]     = useState(DEFAULT_SCRIPT);
  const [running,    setRunning]    = useState(false);
  const [validating, setValidating] = useState(false);
  const [compiling,  setCompiling]  = useState(false);
  const [error,      setError]      = useState(null);
  const [validation, setValidation] = useState(null);
  const [compiledIR, setCompiledIR] = useState(null);
  const navigate = useNavigate();

  function handleScriptChange(e) {
    setScript(e.target.value);
    setValidation(null);
    setError(null);
    setCompiledIR(null);
  }

  async function handleValidate() {
    setError(null);
    setValidation(null);
    setCompiledIR(null);
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

  async function handleCompile() {
    setError(null);
    setCompiledIR(null);
    setCompiling(true);
    try {
      const result = await api.compileScript(script);
      setCompiledIR(result);
    } catch (e) {
      setError(e.message);
    } finally {
      setCompiling(false);
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

  const busy = running || validating || compiling;

  return (
    <div>
      <h1 className="page-title">New Investigation</h1>

      {error      && <div className="msg msg-error"><strong>Error:</strong> {error}</div>}
      {validation && <ValidationSuccess result={validation} />}
      {compiledIR && <CompiledIR result={compiledIR} />}

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
        <strong>Rules:</strong> suspicious_processes · missing_paths · process_network_correlation<br />
        <strong>Platform:</strong> Windows · Ubuntu/Linux — same script, cross-platform execution via Python + psutil
      </div>

      <div className="actions">
        <button className="btn btn-ghost" onClick={handleValidate} disabled={busy || !script.trim()}>
          {validating ? "Validating…" : "✓  Validate"}
        </button>
        <button className="btn btn-ghost" onClick={handleCompile} disabled={busy || !script.trim()}>
          {compiling ? "Compiling…" : "⚙  Compile IR"}
        </button>
        <button className="btn btn-primary" onClick={handleRun} disabled={busy || !script.trim()}>
          {running ? "Running…" : "▶  Run Investigation"}
        </button>
      </div>
    </div>
  );
}
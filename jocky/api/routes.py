"""
API routes for running JOCKY investigations.

This module wires the HTTP layer to the language pipeline
(lexer -> parser -> interpreter), the report builder, and storage. It
does not contain any forensic or parsing logic itself - it only
translates between HTTP requests/responses and the functions we
already built.
"""

import hashlib
from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from fastapi.responses import HTMLResponse, Response
from jocky.reports.encryptor import encrypt_report

from jocky.language.lexer import tokenize, LexError
from jocky.language.parser import parse, ParseError
from jocky.language.interpreter import run_investigation, InterpreterError, CollectorResult
from jocky.language.ir import CollectCommand, AnalyzeCommand, ReportCommand
from jocky.reports.builder import build_report
from jocky.reports.html_writer import build_html_string
from jocky.reports.report import Report
from jocky.analysis.finding import Finding
from jocky.api.schemas import RunInvestigationRequest, InvestigationResponse
from jocky.storage.database import save_investigation, list_investigations, get_investigation
router = APIRouter()


@router.post("/api/investigations", response_model=InvestigationResponse)
def create_investigation(request: RunInvestigationRequest) -> InvestigationResponse:
    """
    Validate and run a JOCKY script, persist the result, and return the
    full report.
    """
    try:
        tokens = tokenize(request.script)
        investigation = parse(tokens)
    except LexError as exc:
        raise HTTPException(status_code=400, detail=f"Lexer error: {exc}")
    except ParseError as exc:
        raise HTTPException(status_code=400, detail=f"Parser error: {exc}")
    script_hash = hashlib.sha256(request.script.encode()).hexdigest()
    started_at = datetime.now(timezone.utc)
    try:
        result = run_investigation(investigation)
    except InterpreterError as exc:
        raise HTTPException(status_code=400, detail=f"Interpreter error: {exc}")
    finished_at = datetime.now(timezone.utc)

    report = build_report(result, started_at, finished_at, script_hash=script_hash)
    report_dict = asdict(report)

    new_id = save_investigation(
        investigation_name=report.investigation_name,
        endpoint_hostname=report.endpoint_hostname,
        started_at=report.started_at,
        finished_at=report.finished_at,
        findings_count=len(report.findings),
        report=report_dict,
    )

    return InvestigationResponse(
        id=new_id,
        investigation_name=report.investigation_name,
        endpoint_hostname=report.endpoint_hostname,
        started_at=report.started_at,
        finished_at=report.finished_at,
        findings_count=len(report.findings),
        report_json=report_dict,
    )

@router.post("/api/validate")
def validate_script(request: RunInvestigationRequest) -> dict:
    """
    Validate a JOCKY script without executing it.

    Runs the lexer and parser only. No collectors are called,
    no data is collected, nothing is written to the database.
    Returns a summary of what the script contains if valid,
    or a descriptive error if it is not.
    """
    try:
        tokens = tokenize(request.script)
        investigation = parse(tokens)
    except LexError as exc:
        raise HTTPException(status_code=400, detail=f"Lexer error: {exc}")
    except ParseError as exc:
        raise HTTPException(status_code=400, detail=f"Parser error: {exc}")

    from jocky.language.ir import CollectCommand, AnalyzeCommand, ReportCommand

    collect_count = sum(1 for c in investigation.commands if isinstance(c, CollectCommand))
    analyze_count = sum(1 for c in investigation.commands if isinstance(c, AnalyzeCommand))
    has_report   = any(isinstance(c, ReportCommand) for c in investigation.commands)

    return {
        "valid": True,
        "investigation_name": investigation.name,
        "total_commands": len(investigation.commands),
        "collect_count": collect_count,
        "analyze_count": analyze_count,
        "has_report": has_report,
    }

@router.post("/api/compile")
def compile_script(request: RunInvestigationRequest) -> dict:
    """
    Tokenize and parse a script, then return a human-readable
    representation of the intermediate representation.

    This demonstrates the separation between source text and the
    validated internal form that the interpreter actually executes.
    No collectors are run.
    """
    try:
        tokens = tokenize(request.script)
        investigation = parse(tokens)
    except LexError as exc:
        raise HTTPException(status_code=400, detail=f"Lexer error: {exc}")
    except ParseError as exc:
        raise HTTPException(status_code=400, detail=f"Parser error: {exc}")

    commands = []
    for cmd in investigation.commands:
        commands.append({
            "type": type(cmd).__name__,
            "target": getattr(cmd, "target", None) or getattr(cmd, "name", None),
        })

    import base64, json
    ir_bytes = json.dumps(commands).encode()
    ir_b64   = base64.b64encode(ir_bytes).decode()

    return {
        "investigation_name": investigation.name,
        "token_count": len(tokens),
        "command_count": len(commands),
        "commands": commands,
        "ir_base64": ir_b64,
    }

@router.get("/api/investigations")
def get_investigations() -> list[dict]:
    """Return summary info for every past investigation, newest first."""
    return list_investigations()


@router.get("/api/investigations/{investigation_id}")
def get_investigation_by_id(investigation_id: int) -> dict:
    """Return the full stored record (including report) for one investigation."""
    record = get_investigation(investigation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return record

@router.get("/api/investigations/{investigation_id}/report.html")
def download_html_report(investigation_id: int) -> HTMLResponse:
    """
    Reconstruct the Report object from the stored JSON and return it
    as a downloadable HTML file. No re-collection happens here — we
    use exactly the evidence that was captured when the investigation ran.
    """
    record = get_investigation(investigation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    rj = record["report_json"]

    # Rebuild the Report dataclass from stored JSON so html_writer can use it.
    report = Report(
        investigation_name=rj["investigation_name"],
        endpoint_hostname=rj["endpoint_hostname"],
        started_at=rj["started_at"],
        finished_at=rj["finished_at"],
        report_name=rj.get("report_name"),
        collector_results=[
            CollectorResult(
                target=cr["target"],
                status=cr["status"],
                data=cr.get("data"),
                error=cr.get("error"),
            )
            for cr in rj.get("collector_results", [])
        ],
        findings=[
            Finding(
                rule_name=f["rule_name"],
                severity=f["severity"],
                summary=f["summary"],
                reason=f["reason"],
                related_evidence=f.get("related_evidence", {}),
            )
            for f in rj.get("findings", [])
        ],
        collector_errors=[],
    )

    html = build_html_string(report)

    filename = f"jocky_report_{investigation_id}.html"
    return HTMLResponse(
        content=html,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.get("/api/investigations/{investigation_id}/report.encrypted")
def download_encrypted_report(investigation_id: int) -> Response:
    """
    Return the JSON report encrypted with AES-256-GCM.

    The encryption key is embedded in the Content-Disposition filename
    as a hex string so the investigator can recover it from download
    metadata. In a production system the key would be stored in a
    separate secure key store.
    """
    record = get_investigation(investigation_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Investigation not found")

    import json
    plaintext = json.dumps(record["report_json"], indent=2).encode()
    ciphertext, key = encrypt_report(plaintext)
    key_hex = key.hex()

    return Response(
        content=ciphertext,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": (
                f'attachment; filename="jocky_report_{investigation_id}.enc"'
            ),
            "X-Encryption": "AES-256-GCM",
            "X-Decryption-Key": key_hex,
        },
    )
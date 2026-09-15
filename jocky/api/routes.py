"""
API routes for running JOCKY investigations.

This module wires the HTTP layer to the language pipeline
(lexer -> parser -> interpreter), the report builder, and storage. It
does not contain any forensic or parsing logic itself - it only
translates between HTTP requests/responses and the functions we
already built.
"""

from dataclasses import asdict
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from jocky.language.lexer import tokenize, LexError
from jocky.language.parser import parse, ParseError
from jocky.language.interpreter import run_investigation, InterpreterError
from jocky.reports.builder import build_report
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

    started_at = datetime.now(timezone.utc)
    try:
        result = run_investigation(investigation)
    except InterpreterError as exc:
        raise HTTPException(status_code=400, detail=f"Interpreter error: {exc}")
    finished_at = datetime.now(timezone.utc)

    report = build_report(result, started_at, finished_at)
    report_dict = asdict(report)

    save_investigation(
        investigation_name=report.investigation_name,
        endpoint_hostname=report.endpoint_hostname,
        started_at=report.started_at,
        finished_at=report.finished_at,
        findings_count=len(report.findings),
        report=report_dict,
    )

    return InvestigationResponse(
        investigation_name=report.investigation_name,
        endpoint_hostname=report.endpoint_hostname,
        started_at=report.started_at,
        finished_at=report.finished_at,
        findings_count=len(report.findings),
        report_json=report_dict,
    )


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
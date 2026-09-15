"""
Pydantic schemas for the JOCKY API.

These define the exact shape of request and response JSON bodies.
FastAPI uses them to validate incoming requests automatically and to
generate the /docs page.
"""

from pydantic import BaseModel


class RunInvestigationRequest(BaseModel):
    script: str  # raw JOCKY DSL source code


class InvestigationResponse(BaseModel):
    id: int                  # database row id — needed to navigate to the detail page
    investigation_name: str
    endpoint_hostname: str
    started_at: str
    finished_at: str
    findings_count: int
    report_json: dict        # the full report, as a plain dict
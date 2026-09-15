"""
Builds a Report from an InvestigationResult by adding timing and
endpoint metadata. This is a pure transformation - it does not write
any files.
"""

import socket
from datetime import datetime, timezone

from jocky.language.interpreter import InvestigationResult
from jocky.reports.report import Report


def build_report(
    result: InvestigationResult,
    started_at: datetime,
    finished_at: datetime,
) -> Report:
    """Assemble a Report from a completed InvestigationResult."""
    collector_errors = [
        cr for cr in result.collector_results if cr.status == "error"
    ]

    return Report(
        investigation_name=result.name,
        endpoint_hostname=socket.gethostname(),
        started_at=started_at.isoformat(),
        finished_at=finished_at.isoformat(),
        collector_results=result.collector_results,
        findings=result.findings,
        report_name=result.report_name,
        collector_errors=collector_errors,
    )
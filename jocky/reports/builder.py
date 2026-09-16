"""
Builds a Report dataclass from an InvestigationResult.

The builder is the only place that knows about both the interpreter
output shape and the Report shape. It does not perform collection or
analysis — it only assembles the final structure.
"""

import platform
from datetime import datetime
from typing import Optional

from jocky.reports.report import Report


def build_report(
    result,
    started_at: datetime,
    finished_at: datetime,
    script_hash: Optional[str] = None,
) -> Report:
    """
    Convert an InvestigationResult into a Report.

    endpoint_hostname is derived here from the local machine because
    InvestigationResult does not carry it — the interpreter runs
    locally so platform.node() is always correct.
    """
    return Report(
        investigation_name=result.name,
        endpoint_hostname=platform.node().upper() or "unknown",
        started_at=started_at.isoformat(),
        finished_at=finished_at.isoformat(),
        collector_results=result.collector_results,
        findings=result.findings,
        collector_errors=[],
        report_name=result.report_name,
        script_hash=script_hash,
    )
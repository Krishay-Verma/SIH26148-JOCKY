"""
Report dataclass — the structured output of one completed investigation.

script_hash: SHA-256 of the JOCKY script source that produced this report.
             Provides a tamper-evident link between the script and its output.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CollectorResult:
    target: str
    status: str        # "success" or "error"
    data: Optional[dict]  = None
    error: Optional[str]  = None


@dataclass
class Finding:
    rule_name: str
    severity: str
    summary: str
    reason: str
    related_evidence: dict = field(default_factory=dict)


@dataclass
class Report:
    investigation_name: str
    endpoint_hostname: str
    started_at: str
    finished_at: str
    collector_results: list
    findings: list
    collector_errors: list
    report_name: Optional[str]  = None
    script_hash: Optional[str]  = None   # SHA-256 of the source script
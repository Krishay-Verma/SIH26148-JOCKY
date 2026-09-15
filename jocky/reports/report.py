"""
Report: the final structured output of a JOCKY investigation.

This is deliberately a plain dataclass, not a class with save/upload
methods - per JOCKY's design rules, "save_report() should not silently
upload data." Building a report and writing it to disk are two
separate, explicit steps (see builder.py and json_writer.py/html_writer.py).
"""

from dataclasses import dataclass, field
from datetime import datetime

from jocky.language.interpreter import InvestigationResult


@dataclass
class Report:
    investigation_name: str
    endpoint_hostname: str
    started_at: str  # ISO timestamp
    finished_at: str  # ISO timestamp
    collector_results: list  # list of CollectorResult (from interpreter.py)
    findings: list             # list of Finding (from analysis/finding.py)
    report_name: str | None = None
    collector_errors: list = field(default_factory=list)  # collectors that failed
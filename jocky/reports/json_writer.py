"""
Writes a Report as JSON.

Uses dataclasses.asdict() to convert the whole Report (including nested
CollectorResult and Finding objects) into plain dicts, since json.dump
can't serialize dataclass instances directly.
"""

import json
from dataclasses import asdict
from pathlib import Path

from jocky.reports.report import Report


def write_json_report(report: Report, output_path: str) -> None:
    """Write report as a formatted JSON file at output_path."""
    data = asdict(report)
    Path(output_path).write_text(json.dumps(data, indent=2), encoding="utf-8")
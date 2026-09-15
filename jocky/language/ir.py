"""
Internal Representation (IR) for parsed JOCKY scripts.

These are plain data structures with no behavior. The parser builds them;
the interpreter later reads them. Keeping IR "dumb" (no methods, no logic)
keeps validation and execution cleanly separated.
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class CollectCommand:
    target: str  # e.g. "system_info", "processes"
    line: int


@dataclass
class AnalyzeCommand:
    rule: str  # e.g. "suspicious_processes"
    line: int


@dataclass
class ReportCommand:
    name: str  # e.g. "triage_report"
    line: int


# A command is one of these three kinds. Using a Union (instead of one
# generic "Command" class with optional fields) means each command only
# ever carries the fields it actually needs.
Command = Union[CollectCommand, AnalyzeCommand, ReportCommand]


@dataclass
class Investigation:
    name: str
    commands: list[Command]
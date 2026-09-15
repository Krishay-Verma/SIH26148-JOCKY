"""
Interpreter for JOCKY investigations.

Walks a validated Investigation (from parser.py) and executes each
command by looking it up in the collector registry or rule registry
(both allowlists). This is the only place in the system where collector
and rule functions actually get called - everything upstream (lexer,
parser) only validates.

Unknown collector/rule names are treated as errors, not silently
skipped, so a typo in a script never produces a misleadingly "clean"
result.
"""

from dataclasses import dataclass, field

from jocky.language.ir import Investigation, CollectCommand, AnalyzeCommand, ReportCommand
from jocky.collectors.registry import get_collector, is_known_collector
from jocky.analysis.registry import get_rule, is_known_rule
from jocky.analysis.finding import Finding


class InterpreterError(Exception):
    """Raised when a command references something not in an allowlist."""
    pass


@dataclass
class CollectorResult:
    target: str
    status: str  # "success" or "error"
    data: dict | None = None
    error: str | None = None


@dataclass
class InvestigationResult:
    name: str
    collector_results: list[CollectorResult] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    report_name: str | None = None


def run_investigation(investigation: Investigation) -> InvestigationResult:
    """
    Execute every command in an Investigation, in order.

    Collector failures (e.g. a permission error inside a collector) are
    caught and recorded per-collector. Unknown collector/rule *names*
    are a hard error, since that indicates a script referencing
    something that was never approved to run.
    """
    result = InvestigationResult(name=investigation.name)

    for command in investigation.commands:
        if isinstance(command, CollectCommand):
            _run_collect(command, result)
        elif isinstance(command, AnalyzeCommand):
            _run_analyze(command, result)
        elif isinstance(command, ReportCommand):
            result.report_name = command.name
        else:
            raise InterpreterError(f"Unhandled command type: {type(command)}")

    return result


def _run_collect(command: CollectCommand, result: InvestigationResult) -> None:
    if not is_known_collector(command.target):
        raise InterpreterError(
            f"Line {command.line}: '{command.target}' is not an approved collector"
        )

    collector_fn = get_collector(command.target)
    try:
        data = collector_fn()
        result.collector_results.append(
            CollectorResult(target=command.target, status="success", data=data)
        )
    except Exception as exc:
        result.collector_results.append(
            CollectorResult(target=command.target, status="error", error=str(exc))
        )


def _run_analyze(command: AnalyzeCommand, result: InvestigationResult) -> None:
    if not is_known_rule(command.rule):
        raise InterpreterError(
            f"Line {command.line}: '{command.rule}' is not an approved analysis rule"
        )

    # Rules read evidence already collected so far in this investigation.
    # Build a simple {target: data} lookup from successful collectors.
    evidence_by_target = {
        cr.target: cr.data
        for cr in result.collector_results
        if cr.status == "success"
    }

    rule_fn = get_rule(command.rule)
    new_findings = rule_fn(evidence_by_target)
    result.findings.extend(new_findings)
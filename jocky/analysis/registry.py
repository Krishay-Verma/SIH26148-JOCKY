"""
Analysis rule registry: the allowlist of rules the interpreter is
permitted to run, mirroring jocky/collectors/registry.py.
"""

from jocky.analysis.rules import (
    rule_missing_executable_path,
    rule_unusual_executable_directory,
    rule_process_network_correlation,
)

RULE_REGISTRY = {
    "suspicious_processes": rule_unusual_executable_directory,
    "missing_paths": rule_missing_executable_path,
    "process_network_correlation": rule_process_network_correlation,
}


def is_known_rule(name: str) -> bool:
    return name in RULE_REGISTRY


def get_rule(name: str):
    if name not in RULE_REGISTRY:
        raise KeyError(f"Unknown analysis rule: {name!r}")
    return RULE_REGISTRY[name]
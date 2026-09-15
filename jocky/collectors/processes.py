"""
Running processes collector.

Lists currently running processes with basic identifying information.
Read-only: iterates OS process info via psutil, never signals or
modifies any process.
"""

import psutil


def collect_processes() -> dict:
    """
    Return a dict with a list of running processes.

    Per-process fields (path, username, start time) can each fail
    independently due to OS permissions — e.g. you often can't read the
    exe path of a SYSTEM process as a normal user. We catch those
    per-field, not per-process, so one restricted field doesn't blank
    out an entire process entry.
    """
    processes = []
    errors = 0

    for proc in psutil.process_iter(["pid", "name"]):
        entry = {
            "pid": proc.info.get("pid"),
            "name": proc.info.get("name"),
            "exe_path": _safe_get(proc, "exe"),
            "username": _safe_get(proc, "username"),
            "start_time": _safe_get(proc, "create_time"),
        }
        if entry["exe_path"] is None or entry["username"] is None:
            errors += 1
        processes.append(entry)

    return {
        "processes": processes,
        "count": len(processes),
        "fields_unavailable": errors,
    }


def _safe_get(proc: psutil.Process, attr: str):
    """Call proc.<attr>() and return None instead of raising on failure."""
    try:
        return getattr(proc, attr)()
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
        return None
"""
System information collector.

Gathers safe, non-sensitive facts about the host machine: hostname, OS,
architecture, CPU/memory basics, and the current username. This function
only reads information — it never modifies the system.
"""

import platform
import socket
import getpass
from datetime import datetime, timezone

import psutil


def collect_system_info() -> dict:
    """
    Return a dictionary of basic system information.

    Uses only standard library `platform`/`socket`/`getpass` plus `psutil`
    for CPU/memory details, since accurate cross-platform hardware info
    isn't reliably available from the standard library alone.
    """
    try:
        current_user = getpass.getuser()
    except Exception:
        current_user = None

    return {
        "hostname": socket.gethostname(),
        "os": platform.system(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "cpu_count": psutil.cpu_count(logical=True),
        "total_memory_bytes": psutil.virtual_memory().total,
        "current_user": current_user,
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
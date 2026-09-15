"""
Network connections collector.

Lists current network connections (local/remote address and port,
status, and owning PID where available). Read-only.
"""

import psutil


def collect_network_connections() -> dict:
    """Return a dict with a list of current network connections."""
    connections = []

    try:
        conns = psutil.net_connections(kind="inet")
    except psutil.AccessDenied:
        return {
            "connections": [],
            "count": 0,
            "error": "Access denied: run with elevated privileges to view all connections",
        }

    for conn in conns:
        local = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None
        remote = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None
        connections.append({
            "local_address": local,
            "remote_address": remote,
            "status": conn.status,
            "pid": conn.pid,
        })

    return {
        "connections": connections,
        "count": len(connections),
    }
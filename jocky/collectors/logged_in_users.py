"""
Logged-in users collector.

Lists currently logged-in user sessions: username, terminal/session
name, and login time. Read-only.
"""

from datetime import datetime, timezone

import psutil


def collect_logged_in_users() -> dict:
    """Return a dict with a list of currently logged-in user sessions."""
    sessions = []

    for user in psutil.users():
        sessions.append({
            "username": user.name,
            "terminal": user.terminal,  # None on Windows; a tty name on Linux
            "host": user.host or None,
            "login_time": datetime.fromtimestamp(
                user.started, tz=timezone.utc
            ).isoformat(),
        })

    return {
        "sessions": sessions,
        "count": len(sessions),
    }
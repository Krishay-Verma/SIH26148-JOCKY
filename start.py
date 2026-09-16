"""
JOCKY Startup Script
--------------------
Starts both the FastAPI backend and the React/Vite frontend
with a single command:

    python start.py

Press Ctrl+C once to shut down both servers cleanly.
"""

import subprocess
import sys
import os
import signal
import time
import platform

IS_WINDOWS = platform.system() == "Windows"

# Colours for terminal output (disabled on Windows if not supported)
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def log(msg, colour=RESET):
    print(f"{colour}{msg}{RESET}", flush=True)

def start_backend():
    """Start uvicorn serving the FastAPI app."""
    cmd = [
        sys.executable, "-m", "uvicorn",
        "jocky.api.main:app",
        "--reload",
        "--port", "8000",
    ]
    return subprocess.Popen(
        cmd,
        cwd=os.path.dirname(os.path.abspath(__file__)),
    )

def start_frontend():
    """Start the Vite dev server inside the frontend/ directory."""
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")

    # On Windows npm is npm.cmd
    npm = "npm.cmd" if IS_WINDOWS else "npm"

    return subprocess.Popen(
        [npm, "run", "dev"],
        cwd=frontend_dir,
    )

def main():
    log(f"\n{BOLD}JOCKY — Forensic Investigation Framework{RESET}")
    log("─" * 42)
    log("Starting backend  →  http://localhost:8000", GREEN)
    log("Starting frontend →  http://localhost:5173", GREEN)
    log("─" * 42)
    log("Press Ctrl+C to stop both servers.\n")

    backend  = start_backend()
    # Give the backend a moment to bind before the frontend starts making requests
    time.sleep(2)
    frontend = start_frontend()

    try:
        backend.wait()
    except KeyboardInterrupt:
        log("\n\nShutting down…", YELLOW)
        backend.terminate()
        frontend.terminate()
        try:
            backend.wait(timeout=5)
            frontend.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend.kill()
            frontend.kill()
        log("Both servers stopped. Goodbye.", GREEN)
        sys.exit(0)

if __name__ == "__main__":
    main()

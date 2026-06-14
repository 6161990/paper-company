#!/usr/bin/env python
"""Start all Paper Company services concurrently."""
import subprocess
import sys
import os

os.chdir("/app")

# Start telegram in background
print("[startup] Starting telegram_poll...", flush=True)
telegram_proc = subprocess.Popen([sys.executable, "scripts/telegram_poll.py"])
print(f"[startup] telegram_poll started (PID: {telegram_proc.pid})", flush=True)

# Start paperclip in foreground (this keeps the container alive)
print("[startup] Starting paperclip_server...", flush=True)
subprocess.call([sys.executable, "scripts/paperclip_server.py"])

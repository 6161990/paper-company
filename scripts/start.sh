#!/bin/bash
set -e

cd /app

echo "Starting Paper Company services..."

# Start all services in background
python scripts/local_runner.py &
RUNNER_PID=$!
echo "Started runner (PID: $RUNNER_PID)"

python scripts/paperclip_server.py &
UI_PID=$!
echo "Started paperclip UI (PID: $UI_PID)"

python scripts/telegram_poll.py &
TELEGRAM_PID=$!
echo "Started telegram poll (PID: $TELEGRAM_PID)"

echo "All services started."

# Keep container alive indefinitely
while true; do
    sleep 3600
done

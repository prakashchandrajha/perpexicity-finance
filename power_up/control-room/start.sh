#!/usr/bin/env bash
# Start Antigravity Control Room (Backend API + React UI)

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 STARTING ANTIGRAVITY INTRADAY CONTROL ROOM"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Kill any existing server on port 8888 or 5173
lsof -ti:8888 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

echo "1. Launching Backend API Bridge on http://127.0.0.1:8888..."
python3 backend_api.py &
BACKEND_PID=$!

echo "2. Launching React UI Dashboard..."
cd project-control-ui
npm run dev &
FRONTEND_PID=$!

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ CONTROL ROOM ACTIVE!"
echo "  Backend API : http://127.0.0.1:8888"
echo "  React UI    : http://localhost:5173"
echo "  Press Ctrl+C to stop both servers."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

trap "kill -9 $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait

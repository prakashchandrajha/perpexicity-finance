#!/usr/bin/env bash
# Start Antigravity Control Room & All 5 Sidecar Bridge Servers

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"
ROOT_DIR="$( cd "$DIR/../.." >/dev/null 2>&1 && pwd )"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 STARTING ANTIGRAVITY 6-ENGINE TRADING BOT TERMINAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 1. Clean up existing ports
echo "🧹 Cleaning old sidecar and control room processes..."
for port in 8765 8776 8777 8778 8787 8888 5173; do
    lsof -ti:$port | xargs kill -9 2>/dev/null
done
sleep 1

# 2. Launch all 5 Extension Bridge Sidecars (handles 6 portals including StockGro)
echo "⚡ Launching Sidecar Bridge Engines..."
python3 "$ROOT_DIR/perplexity-finance-scraper/scraper/extension_server.py" >/dev/null 2>&1 &
PID_PERP=$!

python3 "$ROOT_DIR/power_up/screener/server/extension_server.py" >/dev/null 2>&1 &
PID_SCR=$!

python3 "$ROOT_DIR/power_up/chartink/server/extension_server.py" >/dev/null 2>&1 &
PID_CHK=$!

python3 "$ROOT_DIR/power_up/nse_options/server/extension_server.py" >/dev/null 2>&1 &
PID_NSE=$!

python3 "$ROOT_DIR/power_up/trendlyne/server/extension_server.py" >/dev/null 2>&1 &
PID_TRN=$!

echo "  -> Perplexity AI + StockGro Bridge (Port 8765) [PID $PID_PERP]"
echo "  -> Screener.in Bridge (Port 8776) [PID $PID_SCR]"
echo "  -> Chartink Intraday Bridge (Port 8777) [PID $PID_CHK]"
echo "  -> NSE Options Chain Bridge (Port 8778) [PID $PID_NSE]"
echo "  -> Trendlyne MarketMind AI Bridge (Port 8787) [PID $PID_TRN]"

# 3. Launch Control Room Backend API
echo "🌐 Launching Control Room Backend API on http://127.0.0.1:8888..."
python3 backend_api.py &
BACKEND_PID=$!

# 4. Launch React UI Dashboard
echo "🖥️ Launching React UI Command Deck..."
cd project-control-ui
npm run dev &
FRONTEND_PID=$!

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ ALL 6 TRADING ENGINES & CONTROL DECK ACTIVE!"
echo "  Backend API : http://127.0.0.1:8888"
echo "  React UI    : http://localhost:5173"
echo "  Press Ctrl+C to stop all 7 servers cleanly."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

trap "kill -9 $PID_PERP $PID_SCR $PID_CHK $PID_NSE $PID_TRN $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM
wait

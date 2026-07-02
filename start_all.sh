#!/bin/bash
echo "🚀 Starting all 5 Extension Servers..."
nohup python3 power_up/screener/server/extension_server.py > /dev/null 2>&1 &
nohup python3 power_up/chartink/server/extension_server.py > /dev/null 2>&1 &
nohup python3 power_up/nse_options/server/extension_server.py > /dev/null 2>&1 &
nohup python3 power_up/trendlyne/server/extension_server.py > /dev/null 2>&1 &
nohup python3 perplexity-finance-scraper/scraper/extension_server.py > /dev/null 2>&1 &
sleep 2
echo "✅ Active extension servers:"
lsof -i :8765 -i :8776 -i :8777 -i :8778 -i :8787

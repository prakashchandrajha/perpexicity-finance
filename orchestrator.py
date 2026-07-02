#!/usr/bin/env python3
"""
Master Orchestrator - Trading Bot Brain & Command Center
Routes CLI commands to specialized sub-orchestrator modules.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to path if needed
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sub_orchestrators.briefings import cmd_pre_market, cmd_pre_open, cmd_war_room, cmd_journal
from sub_orchestrators.live_loop import cmd_anomaly, cmd_custom_screen, cmd_live_loop
from sub_orchestrators.wicket_keeper import cmd_monitor
from sub_orchestrators.paper_umpire import cmd_paper_entry, cmd_paper_list


def main() -> None:
    parser = argparse.ArgumentParser(description="Master Orchestrator - Trading Bot Brain")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("pre-market", help="Run overnight screens and fetch AI narratives")

    anomaly_parser = subparsers.add_parser("anomaly", help="Investigate a live market anomaly")
    anomaly_parser.add_argument("ticker", help="Stock ticker (e.g. RELIANCE.NS)")
    anomaly_parser.add_argument("--context", required=True, help="What the anomaly is, e.g. 'Volume spiked 5x on a 2 percent drop'")

    custom_parser = subparsers.add_parser("custom-screen", help="Run a dynamic query and investigate results")
    custom_parser.add_argument("query", help="Screener query string")

    live_loop_parser = subparsers.add_parser("live-loop", help="Run a continuous Chartink breakout hunting loop")
    live_loop_parser.add_argument("scanner", help="Chartink scanner name (e.g. 15_min_volume_breakout)")
    live_loop_parser.add_argument("--interval", type=int, default=5, help="Minutes to sleep between scans")

    subparsers.add_parser("monitor", help="Run Wicket-Keeper to check active trade plans and support/stop loss levels")
    subparsers.add_parser("journal", help="Run Video Analyst to inspect historical win-rates and warehouse signals")
    subparsers.add_parser("pre-open", help="Run Pre-Match Pitch Inspection on FII/DII net flows and NIFTY/BANKNIFTY option chains")
    subparsers.add_parser("war-room", help="Run 8:45 AM War Room Briefing on Global Macro, FII flow, and Sector rotation")
    subparsers.add_parser("paper-list", help="Run Player 10 Paper Umpire to view active and closed paper trading ledger")
    
    paper_entry_parser = subparsers.add_parser("paper-entry", help="Run Player 10 Paper Umpire to record a simulated trade execution")
    paper_entry_parser.add_argument("ticker", help="Stock ticker (e.g. TATATECH.NS)")
    paper_entry_parser.add_argument("entry", type=float, help="Entry price")
    paper_entry_parser.add_argument("sl", type=float, help="Stop loss floor price")
    paper_entry_parser.add_argument("target", type=float, help="Target price")
    paper_entry_parser.add_argument("--dir", default="BUY", dest="dir_val", help="Trade direction (BUY or SELL)")

    args = parser.parse_args()

    if args.command == "pre-market":
        cmd_pre_market()
    elif args.command == "anomaly":
        cmd_anomaly(args.ticker, args.context)
    elif args.command == "custom-screen":
        cmd_custom_screen(args.query)
    elif args.command == "live-loop":
        cmd_live_loop(args.scanner, args.interval)
    elif args.command == "monitor":
        cmd_monitor()
    elif args.command == "journal":
        cmd_journal()
    elif args.command == "pre-open":
        cmd_pre_open()
    elif args.command == "war-room":
        cmd_war_room()
    elif args.command == "paper-list":
        cmd_paper_list()
    elif args.command == "paper-entry":
        cmd_paper_entry(args.ticker, args.entry, args.sl, args.target, args.dir_val)


if __name__ == "__main__":
    main()

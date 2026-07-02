#!/usr/bin/env python3
from __future__ import annotations

import time
import uuid
from sub_orchestrators.config import init_paper_trades_db


def cmd_paper_entry(ticker: str, entry: float, sl: float, target: float, direction: str = "BUY") -> None:
    print(f"=== PLAYER 10 (PAPER UMPIRE): RECORDING TRADE FOR {ticker} ===")
    conn = init_paper_trades_db()
    cursor = conn.cursor()
    
    capital = 100000.0  # Simulated ₹1 Lakh standard lot
    qty = max(1, int(capital / entry))
    actual_capital = round(qty * entry, 2)
    trade_id = f"PTR_{uuid.uuid4().hex[:8].upper()}"
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO paper_trades (trade_id, ticker, direction, entry_price, stop_loss, target_price, position_size, capital_invested, status, entry_timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'OPEN', ?)
    """, (trade_id, ticker, direction.upper(), entry, sl, target, qty, actual_capital, ts))
    conn.commit()
    conn.close()
    
    print(f"✅ Paper Trade Recorded -> ID: {trade_id} | Ticker: {ticker} | Dir: {direction.upper()} | Qty: {qty} | Entry: ₹{entry} | SL: ₹{sl} | Target: ₹{target}")
    print(f"   Simulated Capital Invested: ₹{actual_capital:,.2f}")
    print("   Run 'python3 orchestrator.py monitor' to let the Wicket-Keeper manage this trade automatically!")


def cmd_paper_list() -> None:
    print("=== PLAYER 10 (PAPER UMPIRE): ACTIVE & HISTORICAL LEDGER ===")
    conn = init_paper_trades_db()
    cursor = conn.cursor()
    cursor.execute("SELECT trade_id, ticker, direction, entry_price, stop_loss, target_price, position_size, status, exit_price, pnl_rupees, pnl_pct, entry_timestamp FROM paper_trades ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        print("No paper trades found in SQLite ledger. Use 'python3 orchestrator.py paper-entry <ticker> <entry> <sl> <target>' to start!")
        return
        
    print(f"{'ID':<12} {'TICKER':<12} {'DIR':<6} {'ENTRY':<10} {'SL':<10} {'TARGET':<10} {'STATUS':<12} {'PNL ₹':<10} {'PNL %':<8}")
    print("-" * 95)
    for r in rows:
        t_id, tick, dir_val, ent, sl_val, tgt, qty, stat, ex_p, pnl_r, pnl_p, ts_ent = r
        pnl_r_str = f"{pnl_r:,.2f}" if pnl_r is not None else "-"
        pnl_p_str = f"{pnl_p:.2f}%" if pnl_p is not None else "-"
        print(f"{t_id:<12} {tick:<12} {dir_val:<6} {ent:<10} {sl_val:<10} {tgt:<10} {stat:<12} {pnl_r_str:<10} {pnl_p_str:<8}")
    print("=" * 95)

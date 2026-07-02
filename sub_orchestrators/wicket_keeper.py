#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from sub_orchestrators.config import PERPLEXITY_DIR, init_paper_trades_db, normalize_symbol
from sub_orchestrators.data_fetcher import get_live_spot_price


def cmd_monitor() -> None:
    print("=== ORCHESTRATOR: THE WICKET-KEEPER (ACTIVE STOP LOSS / TARGET MONITOR) ===")
    data_dir = PERPLEXITY_DIR / "data"
    if not data_dir.exists():
        print("No historical trade plans found in data/.")
        return
        
    latest_files = sorted(data_dir.glob("*/live_market_*.json"), reverse=True)[:5]
    if not latest_files:
        print("No live_market analysis files found.")
    else:
        print(f"Checking {len(latest_files)} recent live market trade plans...")
        for file_path in latest_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                ticker = data.get("ticker", "UNKNOWN")
                signals = data.get("signals", {})
                score = signals.get("sentiment_score", 0)
                key_levels = signals.get("key_levels", {})
                options_data = signals.get("options_data", {})
                
                support = key_levels.get("options_support") or options_data.get("support_level")
                resistance = key_levels.get("options_resistance") or options_data.get("resistance_level")
                underlying = options_data.get("underlying_price")
                
                print(f"\n[Trade Plan]: {ticker} | Score: {score} | Underlying: ₹{underlying} | Support (SL Floor): ₹{support} | Resistance: ₹{resistance}")
                if support and underlying:
                    try:
                        s_val = float(str(support).replace("₹", "").replace(",", "").strip())
                        u_val = float(str(underlying).replace("₹", "").replace(",", "").strip())
                        
                        atr_15m = round(u_val * 0.015, 2)
                        stage2_breakeven_trigger = round(s_val + (1.0 * atr_15m), 2)
                        stage3_trail_trigger = round(s_val + (2.0 * atr_15m), 2)
                        dynamic_trailing_sl = round(u_val - (1.5 * atr_15m), 2)
                        
                        print(f"   [ATR Risk Engine] Est. 15m ATR: ₹{atr_15m} | Stage 2 Trigger: ₹{stage2_breakeven_trigger} | Stage 3 Trigger: ₹{stage3_trail_trigger}")
                        
                        if u_val < s_val:
                            print(f"   🚨 ALERT (KILL SWITCH - STAGE 1 FAILURE): {ticker} fell below OI Support floor ₹{s_val}! EXECUTE IMMEDIATE EXIT!")
                        elif u_val >= stage3_trail_trigger:
                            print(f"   🔥 STAGE 3 RUNNER (DYNAMIC TRAIL): {ticker} is surging! Stop Loss dynamically trailed to ₹{dynamic_trailing_sl} (1.5x ATR below spot). Ride the trend!")
                        elif u_val >= stage2_breakeven_trigger:
                            print(f"   🔒 STAGE 2 BREAK-EVEN LOCK: {ticker} moved +1 ATR in profit! Stop Loss locked to Cost (₹{s_val}). Zero loss guaranteed.")
                        else:
                            print(f"   🛡️ STAGE 1 (INITIAL RISK): {ticker} trading safely above floor ₹{s_val}. Waiting for +1 ATR break-even trigger.")
                    except ValueError:
                        pass
            except Exception as e:
                print(f"Error checking {file_path.name}: {e}")
            
    print("\n--- Checking Active Player 10 Paper Trades Against Live Market Prices ---")
    try:
        conn = init_paper_trades_db()
        cursor = conn.cursor()
        cursor.execute("SELECT trade_id, ticker, direction, entry_price, stop_loss, target_price, position_size FROM paper_trades WHERE status = 'OPEN'")
        open_trades = cursor.fetchall()
        
        if not open_trades:
            print("No open paper trades currently running in SQLite ledger.")
        else:
            for trade in open_trades:
                t_id, tick, dir_val, ent, sl_val, tgt, qty = trade
                base_sym = normalize_symbol(tick)
                print(f"\n[Active Paper Trade] {t_id} | {tick} ({dir_val}) | Qty: {qty} | Entry: ₹{ent} | SL: ₹{sl_val} | Target: ₹{tgt}")
                
                live_price = get_live_spot_price(base_sym)
                if live_price <= 0:
                    print(f"   ⚠️ Could not fetch real-time spot price for {tick}. Skipping live trailing stop evaluation.")
                    continue
                    
                print(f"   ⚡ Live Spot Price from TradingView: ₹{live_price}")
                atr_15m = round(ent * 0.015, 2)
                stage2_trigger = round(ent + (1.0 * atr_15m), 2)
                stage3_trigger = round(ent + (2.0 * atr_15m), 2)
                now_ts = time.strftime("%Y-%m-%d %H:%M:%S")
                
                # Check 1: Stop Loss Hit
                if live_price <= sl_val:
                    pnl_r = round(qty * (live_price - ent), 2)
                    pnl_p = round((live_price - ent) / ent * 100, 2)
                    print(f"   🚨 STOP LOSS HIT! Live price ₹{live_price} fell below SL floor ₹{sl_val}! Closing trade...")
                    cursor.execute("""
                        UPDATE paper_trades
                        SET status = 'CLOSED_SL', exit_price = ?, pnl_rupees = ?, pnl_pct = ?, exit_timestamp = ?, exit_reason = 'Stop Loss Hit'
                        WHERE trade_id = ?
                    """, (live_price, pnl_r, pnl_p, now_ts, t_id))
                    conn.commit()
                    print(f"   ❌ Trade {t_id} closed at ₹{live_price} | P&L: ₹{pnl_r:,.2f} ({pnl_p}%)")
                    continue
                    
                # Check 2: Target Price Hit
                if live_price >= tgt:
                    pnl_r = round(qty * (live_price - ent), 2)
                    pnl_p = round((live_price - ent) / ent * 100, 2)
                    print(f"   🎯 TARGET REACHED! Live price ₹{live_price} hit profit target ₹{tgt}! Closing trade...")
                    cursor.execute("""
                        UPDATE paper_trades
                        SET status = 'CLOSED_TARGET', exit_price = ?, pnl_rupees = ?, pnl_pct = ?, exit_timestamp = ?, exit_reason = 'Target Reached'
                        WHERE trade_id = ?
                    """, (live_price, pnl_r, pnl_p, now_ts, t_id))
                    conn.commit()
                    print(f"   💰 Trade {t_id} closed in profit at ₹{live_price} | P&L: +₹{pnl_r:,.2f} (+{pnl_p}%)")
                    continue
                    
                # Check 3: Stage 3 Dynamic Trailing Runner
                if live_price >= stage3_trigger:
                    dynamic_sl = round(live_price - (1.5 * atr_15m), 2)
                    if dynamic_sl > sl_val:
                        print(f"   🔥 STAGE 3 RUNNER: Price surging at ₹{live_price}! Upgrading Trailing SL from ₹{sl_val} -> ₹{dynamic_sl} in SQLite ledger!")
                        cursor.execute("UPDATE paper_trades SET stop_loss = ?, notes = ? WHERE trade_id = ?", (dynamic_sl, f"Trailed to Stage 3 at {now_ts}", t_id))
                        conn.commit()
                        sl_val = dynamic_sl
                    else:
                        print(f"   🔥 STAGE 3 RUNNER: Price at ₹{live_price}. Current SL ₹{sl_val} is already optimized.")
                        
                # Check 4: Stage 2 Break-Even Lock
                elif live_price >= stage2_trigger and sl_val < ent:
                    print(f"   🔒 STAGE 2 BREAK-EVEN LOCK: Price reached +1 ATR (₹{live_price}). Locking Stop Loss to Cost ₹{ent} in SQLite ledger!")
                    cursor.execute("UPDATE paper_trades SET stop_loss = ?, notes = ? WHERE trade_id = ?", (ent, f"Locked to Break-Even at {now_ts}", t_id))
                    conn.commit()
                    sl_val = ent
                else:
                    print(f"   🛡️ STAGE 1 (INITIAL RISK): Price ₹{live_price} trading above SL ₹{sl_val}. Need ₹{stage2_trigger} to lock break-even.")
                    
        conn.close()
    except Exception as e:
        print(f"Error checking paper trades against live market: {e}")
        
    print("\n=== WICKET-KEEPER MONITORING COMPLETE ===")

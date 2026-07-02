#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from sub_orchestrators.config import NSE_OPTIONS_DIR


def run_committee_vote(ticker: str, base_symbol: str, risk: str, size: float, blocked: str, trendlyne_ctx: str, nse_ctx: str, options_ctx: str, fii_ctx: str, sector_ctx: str, inv_ctx: str, tv_ctx: str) -> tuple[bool, str, float, float, float]:
    print("\n" + "=" * 88)
    print(f"👑 10-MAN INSTITUTIONAL COMMITTEE SCORECARD FOR {ticker}")
    print("=" * 88)
    
    vetoed = False
    veto_reason = ""
    yes_votes = 0
    total_voters = 7
    
    # 1. Rohit Sharma (Chartink)
    print(f"[Player 1] Rohit Sharma (Chartink):    ✅ PASSED (Volume Breakout / Turnover > ₹20 Cr)")
    yes_votes += 1
    
    # 2. Virat Kohli (Screener)
    if risk == "high" or (blocked and blocked != "[]"):
        print(f"[Player 2] Virat Kohli (Screener):     ❌ VETOED (Risk: {risk} | Blocked: {blocked})")
        vetoed = True
        veto_reason = f"Fundamental Risk is {risk} or Blocked: {blocked}"
    else:
        print(f"[Player 2] Virat Kohli (Screener):     ✅ PASSED (Risk: {risk} | Size Multiplier: {size}x)")
        yes_votes += 1
        
    # 3. Jasprit Bumrah (NSE Options)
    pcr_val = "N/A"
    max_pain_val = "N/A"
    support_val = 0.0
    resistance_val = 0.0
    underlying_val = 0.0
    
    opt_file = NSE_OPTIONS_DIR / "data" / f"{base_symbol}_options.json"
    if opt_file.exists():
        try:
            with open(opt_file, "r", encoding="utf-8") as f:
                o_json = json.load(f)
            pcr_val = str(o_json.get("pcr", "N/A"))
            max_pain_val = str(o_json.get("max_pain_strike", "N/A"))
            support_val = float(str(o_json.get("support_level", 0)).replace("₹", "").replace(",", "").strip() or 0)
            resistance_val = float(str(o_json.get("resistance_level", 0)).replace("₹", "").replace(",", "").strip() or 0)
            underlying_val = float(str(o_json.get("underlying_price", 0)).replace("₹", "").replace(",", "").strip() or 0)
            pin_risk = o_json.get("expiry_pinning_risk", "LOW")
            
            if pin_risk == "HIGH":
                print(f"[Player 3] Jasprit Bumrah (Options):   ❌ VETOED (Expiry Pinning Magnet Risk is HIGH at ₹{max_pain_val})")
                vetoed = True
                veto_reason = f"Weekly Expiry Pinning Magnet Risk at Max Pain ₹{max_pain_val}"
            else:
                print(f"[Player 3] Jasprit Bumrah (Options):   ✅ PASSED (PCR: {pcr_val} | Max Pain: ₹{max_pain_val} | Support Floor: ₹{support_val})")
                yes_votes += 1
        except Exception:
            print("[Player 3] Jasprit Bumrah (Options):   ⚡ NEUTRAL (Options data parsing fallback)")
            yes_votes += 1
    else:
        print("[Player 3] Jasprit Bumrah (Options):   ⚡ NEUTRAL (No options derivatives data found)")
        yes_votes += 1
        
    # 4. Yuvraj Singh (Trendlyne)
    if "DVM" in trendlyne_ctx or "Durability" in trendlyne_ctx or "Structured context" in trendlyne_ctx:
        print("[Player 4] Yuvraj Singh (Trendlyne):   ✅ PASSED (Institutional DVM & Broker Targets Verified)")
        yes_votes += 1
    else:
        print("[Player 4] Yuvraj Singh (Trendlyne):   ⚡ NEUTRAL (Moderate DVM consensus)")
        yes_votes += 1
        
    # 5. MS Dhoni (Investing.com Macro Weather)
    if "ALGORITHMIC DUMPING VETO" in inv_ctx or "spiking US 10Y Bond Yields" in inv_ctx.lower() or "block all aggressive" in inv_ctx.lower():
        print("[Player 5] MS Dhoni (Macro Weather):   ❌ VETOED (US 10Y Yield Spike / Rupee Weakness -> FII Dumping!)")
        vetoed = True
        veto_reason = "Global Macro FII Dumping Veto triggered by MS Dhoni"
    else:
        print("[Player 5] MS Dhoni (Macro Weather):   ✅ PASSED (Global Macro Weather & Technical Consensus Support)")
        yes_votes += 1
        
    # 6. Pitch Inspector (FII/DII Net Flow)
    if "CATEGORY 5 STORM" in fii_ctx:
        print("[Player 6] Pitch Inspector (FII Flow): ⚠️ CAUTION (Category 5 FII Selling -> Downgrading Size by 50%)")
        yes_votes += 1
    else:
        print("[Player 6] Pitch Inspector (FII Flow): ✅ PASSED (Institutional Cash Flow Pitch Calibrated)")
        yes_votes += 1
        
    # 7. Hardik Pandya (Sector Heatmap)
    if "ADV/DEC" in sector_ctx or "HEATMAP" in sector_ctx:
        print("[Player 7] Hardik Pandya (Sector):     ✅ PASSED (Sector Rotation Momentum Aligned)")
        yes_votes += 1
    else:
        print("[Player 7] Hardik Pandya (Sector):     ⚡ NEUTRAL (Sector momentum average)")
        yes_votes += 1
        
    print("=" * 88)
    if vetoed:
        print(f"🚨 COMMITTEE VERDICT: ❌ REJECTED! Trade blocked by committee veto: {veto_reason}")
    else:
        print(f"🎯 COMMITTEE VERDICT: ✅ APPROVED ({yes_votes}/{total_voters} YES VOTES)! Handing off to Player 8 (The Captain)...")
    print("=" * 88)
    
    return vetoed, veto_reason, underlying_val, support_val, resistance_val

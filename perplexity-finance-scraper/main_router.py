import argparse
import asyncio
from engine.router import SmartRouter

async def run():
    parser = argparse.ArgumentParser(description="Smart Engine Router")
    parser.add_argument("playbook", choices=["scalp", "swing", "ideas"], help="Playbook to execute")
    parser.add_argument("--ticker", type=str, help="Ticker to analyze (required for scalp/swing)", default=None)
    
    args = parser.parse_args()
    
    router = SmartRouter()
    
    if args.playbook == "ideas":
        print(f"\\n=== EXECUTING IDEA GENERATION PLAYBOOK ===")
        res = await router.generate_ideas()
        print(res)
    elif args.playbook == "scalp":
        if not args.ticker:
            print("Error: --ticker is required for scalping")
            return
        print(f"\\n=== EXECUTING SCALP PLAYBOOK FOR {args.ticker} ===")
        res = await router.play_scalp(args.ticker)
        print(f"\\n> NSE DATA: {res['options']}")
        print(f"\\n> NARRATIVE EDGE: {res['narrative']}")
    elif args.playbook == "swing":
        if not args.ticker:
            print("Error: --ticker is required for swinging")
            return
        print(f"\\n=== EXECUTING SWING PLAYBOOK FOR {args.ticker} ===")
        res = await router.play_swing(args.ticker)
        print(f"\\n> QUANT DATA: {res['quant']}")
        print(f"\\n> NARRATIVE EDGE: {res['narrative']}")

if __name__ == "__main__":
    asyncio.run(run())

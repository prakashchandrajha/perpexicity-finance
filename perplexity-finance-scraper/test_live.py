import asyncio
from bot_api import PerplexityTraderAPI

async def run():
    api = PerplexityTraderAPI()
    print("Running live_market for OFSS...")
    res = await api.analyze("OFSS", "live_market", "Double cross-question: Any hidden risks or breaking news?", save_to_db=False)
    print("Result:", res)

asyncio.run(run())

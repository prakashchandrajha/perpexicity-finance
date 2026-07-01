import re
from scraper.extension_client import PerplexityExtensionClient
from loguru import logger

class StockGroBogie:
    def __init__(self, client: PerplexityExtensionClient):
        self.client = client
        self.js_script = """
function() {
    try {
        const data = {};
        data.url = window.location.href;
        data.pageTitle = document.title;
        
        const navLinks = Array.from(document.querySelectorAll('a')).map(a => a.href);
        data.navLinks = [...new Set(navLinks)];
        
        const textBlocks = Array.from(document.querySelectorAll('div, span, p, h1, h2, h3'))
            .filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0 && el.innerText && el.innerText.trim().length > 0;
            })
            .map(el => el.innerText.trim());
            
        data.visibleTextSample = [...new Set(textBlocks)].slice(0, 50);
        return data;
    } catch(e) {
        return { error: "extractStockGroData error: " + e.message };
    }
}()
        """

    def extract_ideas(self) -> dict:
        """
        Runs the StockGro extraction playbook.
        """
        logger.info("[StockGro Bogie] Extracting ideas...")
        
        try:
            import requests
            res = requests.post(f"http://127.0.0.1:8765/queue_job", json={
                "type": "execute_named_function",
                "url": "https://app.stockgro.club/ui/home",
                "script": "extractStockGroData",
                "args": [],
                "wait_ms": 4000
            })
            job_id = res.json().get("job_id")
            result = self.client._wait_for_result(job_id, timeout=30)
        except Exception as e:
            result = {"error": str(e)}
        
        if "error" in result:
            return {"error": result["error"]}
            
        parsed_data = {
            "high_upside_stocks": [],
            "trade_ideas": [],
            "tickers": set(),
            "raw_sample": result.get("visibleTextSample", [])
        }
        
        text_blocks = result.get("visibleTextSample", [])
        for text in text_blocks:
            if "Potential\nUpside" in text:
                parsed_data["high_upside_stocks"].append(text.split("\n\n")[0])
            if "profit in" in text or "Profit Achieved" in text:
                parsed_data["trade_ideas"].append(text.split("\n\n")[0])
            
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if re.match(r'^[A-Z]{3,10}$', line):
                    if line not in ["NIFTY", "OPTIONS", "STOCKS"]:
                        parsed_data["tickers"].add(line)
                        
        parsed_data["tickers"] = list(parsed_data["tickers"])
        return parsed_data

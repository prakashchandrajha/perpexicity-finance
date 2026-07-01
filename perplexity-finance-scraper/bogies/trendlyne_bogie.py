from scraper.extension_client import PerplexityExtensionClient
from loguru import logger
import requests

class TrendlyneBogie:
    def __init__(self, client: PerplexityExtensionClient):
        self.client = client
        self.js_script = """
function(ticker) {
    return new Promise((resolve) => {
        try {
            const searchInput = document.querySelector('input[placeholder*="Search Stock"], input[name="q"], .tl-search-input');
            if (!searchInput) {
                resolve({ error: "Trendlyne search bar not found" });
                return;
            }
            
            searchInput.focus();
            searchInput.value = "";
            document.execCommand('insertText', false, ticker);
            
            setTimeout(() => {
                const dropdownItems = document.querySelectorAll('.ui-menu-item a, .search-result-item');
                let found = null;
                for (let item of dropdownItems) {
                    if (item.innerText.toLowerCase().includes(ticker.toLowerCase())) {
                        found = item;
                        break;
                    }
                }
                if (!found && dropdownItems.length > 0) found = dropdownItems[0];
                
                if (found) {
                    found.click();
                    
                    // Wait for page load then extract
                    setTimeout(() => {
                        try {
                            const dvmScore = document.querySelector('.dvm-score, .score-container')?.innerText || "DVM Score not found";
                            const metrics = Array.from(document.querySelectorAll('.metric-item, .alert-item')).map(m => m.innerText);
                            const durability = document.querySelector('div[title*="Durability"]')?.innerText || "N/A";
                            const valuation = document.querySelector('div[title*="Valuation"]')?.innerText || "N/A";
                            const momentum = document.querySelector('div[title*="Momentum"]')?.innerText || "N/A";
                            const alerts = Array.from(document.querySelectorAll('.tl-alert, .technical-alert')).map(el => el.innerText);

                            resolve({
                                dvm_score_raw: dvmScore,
                                durability: durability,
                                valuation: valuation,
                                momentum: momentum,
                                alerts: alerts,
                                metrics: metrics,
                                url: window.location.href
                            });
                        } catch (e) {
                            resolve({ error: "extractTrendlyneData error: " + e.message });
                        }
                    }, 4000); // Wait for SPA navigation to finish
                } else {
                    resolve({ error: "Ticker not found in dropdown" });
                }
            }, 2000);
        } catch(e) {
            resolve({ error: "executeTrendlyneSearch error: " + e.message });
        }
    });
}
        """

    def analyze_quant(self, ticker: str) -> dict:
        logger.info(f"[Trendlyne Bogie] Analyzing Quant for {ticker}...")
        
        try:
            res = requests.post(f"http://127.0.0.1:8765/queue_job", json={
                "type": "execute_named_function",
                "url": "https://trendlyne.com/",
                "script": "executeTrendlyneSearch",
                "args": [ticker],
                "wait_ms": 0
            })
            job_id = res.json().get("job_id")
            search_result = self.client._wait_for_result(job_id, timeout=30)
            
            # Now we extract
            res = requests.post(f"http://127.0.0.1:8765/queue_job", json={
                "type": "execute_named_function",
                "url": "https://trendlyne.com/",
                "script": "extractTrendlyneData",
                "args": [],
                "wait_ms": 4000
            })
            job_id = res.json().get("job_id")
            extract_result = self.client._wait_for_result(job_id, timeout=30)
            
            return extract_result
        except Exception as e:
            return {"error": str(e)}

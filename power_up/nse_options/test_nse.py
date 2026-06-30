from playwright.sync_api import sync_playwright
import time
import json

def fetch_nse():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.nseindia.com/option-chain")
        time.sleep(5)
        
        # intercept and fetch
        res = page.evaluate("""async () => {
            try {
                let r = await fetch('/api/option-chain-indices?symbol=NIFTY');
                if (r.status === 404) {
                    r = await fetch('/api/option-chain-equities?symbol=RELIANCE');
                }
                let data = await r.json();
                return JSON.stringify(data).substring(0, 500);
            } catch(e) {
                return e.toString();
            }
        }""")
        print(res)
        browser.close()

fetch_nse()

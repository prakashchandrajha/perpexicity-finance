import json
from playwright.async_api import async_playwright, Response
from loguru import logger
from config import PERPLEXITY_URL, HEADLESS, PAGE_TIMEOUT, DATA_WAIT_SECONDS


class BrowserError(Exception):
    pass


class PerplexityBrowser:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=HEADLESS,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await self.browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1920, "height": 1080},
            locale="en-US",
        )
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        self.page = await context.new_page()
        self.page.set_default_timeout(PAGE_TIMEOUT)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def get_ticker_data(self, ticker: str) -> dict:
        """Navigate to /finance/{ticker} and intercept REST API responses.

        Returns a dict keyed by API endpoint name (e.g. "quote/NVDA",
        "profile/NVDA") with parsed JSON values.
        """
        captured: dict[str, dict] = {}

        async def _on_response(resp: Response) -> None:
            if "/rest/finance/" not in resp.url:
                return
            if resp.status != 200:
                return
            try:
                body = await resp.text()
                if not body or body.startswith("<!DOCTYPE"):
                    return
                # Extract key like "quote/NVDA" from full URL
                path = resp.url.split("/rest/finance/")[-1]
                key = path.split("?")[0]
                captured[key] = json.loads(body)
                logger.debug(f"Captured API: {key} ({len(body)} bytes)")
            except Exception as e:
                logger.warning(f"Failed to capture {resp.url}: {e}")

        self.page.on("response", _on_response)

        try:
            url = f"{PERPLEXITY_URL}/{ticker}"
            
            # Retry loop for ERR_NETWORK_CHANGED
            for attempt in range(3):
                try:
                    await self.page.goto(url, wait_until="domcontentloaded")
                    break
                except Exception as e:
                    if "ERR_NETWORK_CHANGED" in str(e) and attempt < 2:
                        logger.warning(f"Network changed, retrying... ({attempt + 1}/3)")
                        import asyncio
                        await asyncio.sleep(2)
                    else:
                        raise
                        
            logger.info(f"Navigated to {url}")

            # Wait for API responses to arrive
            await self.page.wait_for_timeout(DATA_WAIT_SECONDS * 1000)
            logger.info(
                f"Waited {DATA_WAIT_SECONDS}s — captured {len(captured)} API responses"
            )

            if not captured:
                raise BrowserError(
                    f"No API data captured for ticker '{ticker}'. "
                    "The ticker may be invalid or the page structure changed."
                )

            return captured

        except BrowserError:
            raise
        except Exception as e:
            logger.error(f"Browser error: {e}")
            raise BrowserError(str(e))
        finally:
            self.page.remove_listener("response", _on_response)

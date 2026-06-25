import asyncio
import urllib.parse
from loguru import logger
from camoufox.async_api import AsyncCamoufox
from config import PERPLEXITY_URL, HEADLESS


class BrowserError(Exception):
    pass


class PerplexityBrowser:
    """Camoufox-powered browser that queries Perplexity's conversational AI
    and extracts the generated prose response.

    Camoufox uses a patched Firefox with randomized fingerprints to bypass
    Cloudflare Turnstile without any API key.
    """

    def __init__(self):
        self._browser_ctx = None
        self._browser = None

    async def __aenter__(self):
        self._browser_ctx = AsyncCamoufox(headless=HEADLESS)
        self._browser = await self._browser_ctx.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self._browser_ctx:
            await self._browser_ctx.__aexit__(exc_type, exc, tb)

    async def ask(self, prompt: str, timeout: int = 45) -> str:
        """Send a prompt to Perplexity search and return the AI-generated text.

        Args:
            prompt: The exact question to ask Perplexity.
            timeout: Max seconds to wait for the AI response to stream.

        Returns:
            The extracted prose text from Perplexity's answer.
        """
        page = await self._browser.new_page()

        try:
            query = urllib.parse.quote_plus(prompt)
            url = f"{PERPLEXITY_URL}?q={query}"

            logger.info(f"Navigating to Perplexity search...")
            logger.debug(f"URL: {url[:120]}...")

            # Retry loop for transient network errors
            for attempt in range(3):
                try:
                    await page.goto(url, wait_until="domcontentloaded")
                    break
                except Exception as e:
                    if attempt < 2:
                        logger.warning(f"Navigation attempt {attempt + 1} failed: {e}. Retrying...")
                        await asyncio.sleep(2)
                    else:
                        raise BrowserError(f"Failed to navigate after 3 attempts: {e}")

            # Wait for the .prose container (Perplexity's answer block)
            logger.info("Waiting for AI response to generate...")
            try:
                await page.wait_for_selector(".prose", timeout=timeout * 1000)
            except Exception:
                raise BrowserError(
                    "Perplexity did not generate a response within timeout. "
                    "The site may be blocking us or experiencing issues."
                )

            # Let the LLM stream finish — wait for text to stabilize
            stable_text = ""
            for _ in range(timeout // 2):
                await asyncio.sleep(2)
                current_text = await page.locator(".prose").first.inner_text()
                if current_text == stable_text and len(current_text) > 50:
                    break
                stable_text = current_text
            else:
                # Use whatever we have after the loop
                stable_text = await page.locator(".prose").first.inner_text()

            if not stable_text or len(stable_text) < 30:
                raise BrowserError("Perplexity returned an empty or very short response.")

            logger.info(f"Extracted {len(stable_text)} chars of AI-generated prose.")
            return stable_text.strip()

        except BrowserError:
            raise
        except Exception as e:
            logger.error(f"Browser error: {e}")
            raise BrowserError(str(e))
        finally:
            await page.close()

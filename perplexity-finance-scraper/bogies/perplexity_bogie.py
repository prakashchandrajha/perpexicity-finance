from scraper.extension_client import PerplexityExtensionClient
from loguru import logger
import requests

class PerplexityBogie:
    def __init__(self, client: PerplexityExtensionClient):
        self.client = client
        self.js_script = """
function(query) {
    return new Promise((resolve) => {
        try {
            let attempts = 0;
            
            const findDeep = (selector, root = document) => {
                if (root.querySelector(selector)) return root.querySelector(selector);
                for (const el of root.querySelectorAll('*')) {
                    if (el.shadowRoot) {
                        const found = findDeep(selector, el.shadowRoot);
                        if (found) return found;
                    }
                }
                return null;
            };

            const findInterval = setInterval(() => {
                try {
                    // Kill any blocking Radix modals/dialogs continuously
                    document.querySelectorAll('[data-radix-focus-guard], [role="dialog"], [id^="radix-"]').forEach(el => el.remove());
                    document.body.style.pointerEvents = 'auto';
                    document.body.removeAttribute('data-aria-hidden');
                    document.getElementById('root')?.removeAttribute('aria-hidden');

                    const inputElement = findDeep('textarea, [contenteditable="true"], input[type="text"], input[placeholder*="Ask"]');
                    if (inputElement) {
                        clearInterval(findInterval);
                        typeAndSubmit(inputElement);
                    } else if (attempts > 40) { // 20 seconds
                        clearInterval(findInterval);
                        resolve("Error: Could not find search bar (Timeout after 20s).");
                    }
                    attempts++;
                } catch (e) {
                    clearInterval(findInterval);
                    resolve("Error in findInterval: " + e.message);
                }
            }, 500);

            function typeAndSubmit(inputElement) {
                try {
                    // Attempt to auto-enable Pro Search
                    try {
                        const allButtons = Array.from(document.querySelectorAll('button'));
                        const proToggle = allButtons.find(b => {
                            const isProText = (b.innerText || "").toLowerCase().includes('pro');
                            const parentText = (b.parentElement && b.parentElement.innerText || "").toLowerCase();
                            const isUnchecked = b.getAttribute('aria-checked') === 'false';
                            const isSwitch = b.getAttribute('role') === 'switch';
                            return (isProText && isUnchecked) || (isSwitch && isUnchecked && parentText.includes('pro'));
                        });
                        if (proToggle) {
                            proToggle.click();
                        }
                    } catch (e) {}

                    inputElement.focus();
                    if (inputElement.isContentEditable) {
                        while(inputElement.firstChild) inputElement.removeChild(inputElement.firstChild);
                    } else {
                        inputElement.value = "";
                    }
                    document.execCommand('insertText', false, query);

                    setTimeout(() => {
                        try {
                            let parent = inputElement.parentElement;
                            let targetBtn = null;
                            let targetBtnClicked = false;
                            for (let i = 0; i < 6; i++) {
                                if (!parent) break;
                                
                                targetBtn = parent.querySelector('button[type="submit"], button[aria-label*="Submit" i], button[aria-label*="Search" i], button[aria-label*="Send" i]');
                                if (!targetBtn) {
                                    const allBtns = Array.from(parent.querySelectorAll('button'));
                                    targetBtn = allBtns.reverse().find(b => {
                                        const label = (b.getAttribute('aria-label') || "").toLowerCase();
                                        const html = b.innerHTML.toLowerCase();
                                        const isVoice = label.includes("voice") || label.includes("mic") || html.includes("voice") || html.includes("mic");
                                        const isUpload = label.includes("attach") || label.includes("upload") || label.includes("file");
                                        return !isVoice && !isUpload && (b.clientWidth > 0 || b.clientHeight > 0);
                                    });
                                }
                                
                                if (targetBtn) {
                                    targetBtn.click();
                                    targetBtnClicked = true;
                                    break;
                                }
                                parent = parent.parentElement;
                            }

                            if (!targetBtnClicked) {
                                const enterEvent = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true, composed: true });
                                inputElement.dispatchEvent(enterEvent);
                            }
                            
                            let checkCount = 0;
                            let previousLength = 0;
                            let stableCount = 0;

                            const interval = setInterval(() => {
                                try {
                                    checkCount++;
                                    const proseElements = document.querySelectorAll('.prose');
                                    let answerText = "";
                                    
                                    if (proseElements && proseElements.length > 0) {
                                        answerText = Array.from(proseElements).map(el => el.textContent).join('\\n\\n');
                                    } else {
                                        const paragraphs = Array.from(document.querySelectorAll('main p, div[dir="auto"] p, .break-words p')).map(p => p.textContent).join('\\n');
                                        if (paragraphs.length > 50) {
                                            answerText = paragraphs;
                                        }
                                    }

                                    if (answerText.length > 50) {
                                        if (answerText.length === previousLength) {
                                            stableCount++;
                                            if (stableCount >= 3) {
                                                clearInterval(interval);
                                                resolve(answerText);
                                            }
                                        } else {
                                            stableCount = 0;
                                            previousLength = answerText.length;
                                        }
                                    }

                                    if (checkCount > 120) { 
                                        clearInterval(interval);
                                        resolve(answerText.length > 50 ? answerText : "Error: No answer found. Timeout reached.");
                                    }
                                } catch (e) {
                                    clearInterval(interval);
                                    resolve("Error in waitInterval: " + e.message);
                                }
                            }, 1000);
                        } catch (e) {
                            resolve("Error in setTimeout: " + e.message);
                        }
                    }, 500);
                } catch (e) {
                    resolve("Error in typeAndSubmit: " + e.message);
                }
            }
        } catch (e) {
            resolve("Error in executeLiveSearch: " + e.message);
        }
    });
}
        """

    def analyze_narrative(self, query: str, ticker: str = None, use_pro: bool = False) -> str:
        logger.info(f"[Perplexity Bogie] Asking Narrative Engine... (Pro Search: {use_pro})")
        
        # We use the main Perplexity URL because Perplexity Finance does not have dedicated 
        # dashboard pages for many Indian tickers (resulting in 404s). 
        # The main chat interface has full access to live financial data and news.
        url = "https://www.perplexity.ai/"
        
        try:
            res = requests.post(f"http://127.0.0.1:8765/queue_job", json={
                "type": "execute_named_function",
                "url": url,
                "script": "executeLiveSearch",
                "args": [query, use_pro],
                "wait_ms": 0
            })
            job_id = res.json().get("job_id")
            result = self.client._wait_for_result(job_id, timeout=300)
            
            if isinstance(result, dict) and "error" in result:
                return f"Error: {result['error']}"
            
            # If the result itself is a string (the text we want), return it directly.
            if isinstance(result, str):
                return result
                
            return result.get("text", "")
        except Exception as e:
            return f"Error connecting to extension: {e}"

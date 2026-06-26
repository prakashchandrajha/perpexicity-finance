const SERVER_URL = "http://127.0.0.1:8765";
const POLL_INTERVAL_MS = 2000;
let isPolling = false;
let currentTabId = null;

// Visual Badge Indicator
function setBadge(state) {
    try {
        if (state === 'white') {
            chrome.action.setBadgeText({ text: "IDLE" });
            chrome.action.setBadgeBackgroundColor({ color: "#808080" }); // Gray/White means idle
        } else if (state === 'green') {
            chrome.action.setBadgeText({ text: "RUN" });
            chrome.action.setBadgeBackgroundColor({ color: "#00CC00" }); // Green means working
        } else if (state === 'red') {
            chrome.action.setBadgeText({ text: "ERR" });
            chrome.action.setBadgeBackgroundColor({ color: "#FF0000" }); // Red means broken
        }
    } catch(e) {}
}
setBadge('white');

// Keep-Alive listener to prevent MV3 Service Worker suspension
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "KEEP_ALIVE") {
        // Simply receiving this resets the idle timer.
        // Send a dummy response to close the port.
        sendResponse({ ok: true });
    }
});

async function pollForJobs() {
    if (isPolling) return;
    isPolling = true;

    try {
        const response = await fetch(`${SERVER_URL}/get_job`);
        if (response.ok) {
            const job = await response.json();
            if (job && job.job_id) {
                console.log("Received job:", job);
                setBadge('green');
                await handleJob(job);
                // Return to idle after job is fully handled (unless it erred, which is handled below)
            } else {
                setBadge('white');
            }
        } else {
            setBadge('white');
        }
    } catch (e) {
        // Server down
        setBadge('white');
    } finally {
        isPolling = false;
        setTimeout(pollForJobs, POLL_INTERVAL_MS);
    }
}

async function handleJob(job) {
    const { job_id, type, ticker, query } = job;
    let url = "";
    
    if (type === "pre_market" || type === "post_market") {
        url = `https://www.perplexity.ai/finance/${ticker}`;
    } else if (type === "live_market") {
        url = "https://www.perplexity.ai/";
    } else {
        await submitResult(job_id, { error: "Unknown job type" });
        return;
    }

    // Open or update tab
    if (currentTabId) {
        try {
            await chrome.tabs.update(currentTabId, { url, active: false });
        } catch (e) {
            const tab = await chrome.tabs.create({ url, active: true });
            currentTabId = tab.id;
        }
    } else {
        const tab = await chrome.tabs.create({ url, active: true });
        currentTabId = tab.id;
    }

    // Wait for page to load, then execute script
    // Wait for page to load with a timeout
    await new Promise((resolve) => {
        let isResolved = false;
        
        const timeoutId = setTimeout(() => {
            if (!isResolved) {
                isResolved = true;
                chrome.tabs.onUpdated.removeListener(listener);
                resolve();
            }
        }, 8000);

        function listener(tabId, info) {
            if (tabId === currentTabId && info.status === 'complete') {
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    chrome.tabs.onUpdated.removeListener(listener);
                    resolve();
                }
            }
        }
        
        chrome.tabs.get(currentTabId, (tab) => {
            if (tab && tab.status === 'complete') {
                if (!isResolved) {
                    isResolved = true;
                    clearTimeout(timeoutId);
                    resolve();
                }
            } else {
                chrome.tabs.onUpdated.addListener(listener);
            }
        });
    });

    // Short delay to let React hydrate
    await new Promise(r => setTimeout(r, 2000));

    try {
        if (type === "pre_market" || type === "post_market") {
            const results = await chrome.scripting.executeScript({
                target: { tabId: currentTabId },
                func: extractStaticHtml
            });
            await submitResult(job_id, { html: results[0].result });
        } else {
            const results = await chrome.scripting.executeScript({
                target: { tabId: currentTabId },
                func: executeLiveSearch,
                args: [query]
            });
            await submitResult(job_id, { text: results[0].result });
        }
    } catch (e) {
        console.error("Script execution failed", e);
        await submitResult(job_id, { error: e.toString() });
    }
}

async function submitResult(job_id, data) {
    try {
        if (data && data.result && data.result.startsWith("Error")) {
            setBadge('red'); // Ext is not working properly (UI change or timeout)
        } else {
            setBadge('white'); // Success, back to idle
        }
        
        await fetch(`${SERVER_URL}/submit_job/${job_id}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        console.log(`Submitted result for ${job_id}`);
    } catch (e) {
        console.error("Failed to submit result", e);
    }
}

// ── Injected Functions ───────────────────────────────────────────

function extractStaticHtml() {
    return document.documentElement.outerHTML;
}

async function executeLiveSearch(query) {
    return new Promise((resolve) => {
        try {
            let attempts = 0;
            
            // Extreme Precaution: Shadow DOM piercing selector
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

                    // Future-proofed search using Shadow DOM piercing just in case Perplexity switches architecture
                    const inputElement = findDeep('textarea, [contenteditable="true"], input[type="text"], input[placeholder*="Ask"]');
                    if (inputElement) {
                        clearInterval(findInterval);
                        typeAndSubmit(inputElement);
                    } else if (attempts > 10) {
                        clearInterval(findInterval);
                        resolve("Error: Could not find search bar.");
                    }
                    attempts++;
                } catch (e) {
                    clearInterval(findInterval);
                    resolve("Error in findInterval: " + e.message);
                }
            }, 500);

            function typeAndSubmit(inputElement) {
                try {
                    // Holy Grail React Input Injection
                    inputElement.focus();
                    if (inputElement.isContentEditable) {
                        // Clear contenteditable
                        while(inputElement.firstChild) inputElement.removeChild(inputElement.firstChild);
                    } else {
                        inputElement.value = "";
                    }
                    // This triggers all native React onInput/onChange listeners perfectly
                    document.execCommand('insertText', false, query);

                    setTimeout(() => {
                        try {
                            // Try finding the closest button to the input element
                            let parent = inputElement.parentElement;
                            let targetBtn = null;
                            let targetBtnClicked = false;
                            for (let i = 0; i < 6; i++) {
                                if (!parent) break;
                                
                                // First try explicit submit buttons
                                targetBtn = parent.querySelector('button[type="submit"], button[aria-label*="Submit" i], button[aria-label*="Search" i], button[aria-label*="Send" i]');
                                
                                if (!targetBtn) {
                                    // Otherwise grab all buttons and filter out the voice/mic/upload ones
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

                            // Also ALWAYS dispatch Enter key as a fallback, but only if we didn't click
                            if (!targetBtnClicked) {
                                const enterEvent = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true, composed: true });
                                inputElement.dispatchEvent(enterEvent);
                            }
                            
                            // Wait for answer to generate
                            let checkCount = 0;
                            let previousLength = 0;
                            let stableCount = 0;

                            const interval = setInterval(() => {
                                try {
                                    checkCount++;
                                    const proseElements = document.querySelectorAll('.prose');
                                    let answerText = "";
                                    
                                    if (proseElements && proseElements.length > 0) {
                                        answerText = Array.from(proseElements).map(el => el.textContent).join('\n\n');
                                    } else {
                                        const paragraphs = Array.from(document.querySelectorAll('main p, div[dir="auto"] p, .break-words p')).map(p => p.textContent).join('\n');
                                        if (paragraphs.length > 50) {
                                            answerText = paragraphs;
                                        }
                                    }

                                    if (answerText.length > 50) {
                                        // Wait until the text stops changing (i.e. generation is fully complete)
                                        if (answerText.length === previousLength) {
                                            stableCount++;
                                            // If it hasn't changed for 3 seconds, it's done!
                                            if (stableCount >= 3) {
                                                clearInterval(interval);
                                                resolve(answerText);
                                            }
                                        } else {
                                            stableCount = 0;
                                            previousLength = answerText.length;
                                        }
                                    }

                                    // Absolute timeout: 120 seconds for deep financial reports
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

// Start polling
pollForJobs();

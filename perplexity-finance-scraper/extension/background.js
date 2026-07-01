// The Universal Browser Automation Track

const SERVER_URL = "http://127.0.0.1:8765";
let isProcessing = false;
let currentTabId = null;

// Clean badge state
chrome.action.setBadgeBackgroundColor({ color: '#808080' });
chrome.action.setBadgeText({ text: 'IDLE' });

function setBadge(state) {
    if (state === 'active') {
        chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' }); // Green
        chrome.action.setBadgeText({ text: 'RUN' });
    } else if (state === 'red') {
        chrome.action.setBadgeBackgroundColor({ color: '#F44336' }); // Red
        chrome.action.setBadgeText({ text: 'ERR' });
    } else {
        chrome.action.setBadgeBackgroundColor({ color: '#808080' }); // Gray
        chrome.action.setBadgeText({ text: 'IDLE' });
    }
}

async function pollForJobs() {
    if (isProcessing) return;

    try {
        const response = await fetch(`${SERVER_URL}/get_job`);
        if (response.ok) {
            const job = await response.json();
            if (job && job.job_id) {
                isProcessing = true;
                setBadge('active');
                await handleJob(job);
                isProcessing = false;
            }
        }
    } catch (e) {
        // Server might be down, ignore quietly
    }

    // Poll every 2 seconds
    setTimeout(pollForJobs, 2000);
}

async function handleJob(job) {
    const { job_id, type, url, script, wait_ms } = job;
    
    console.log(`[Ext] Received Job ${job_id}: ${type} for ${url}`);

    try {
        // 1. Navigate to target URL
        if (currentTabId) {
            try {
                await chrome.tabs.update(currentTabId, { url: url, active: true });
            } catch (e) {
                const tab = await chrome.tabs.create({ url: url, active: true });
                currentTabId = tab.id;
            }
        } else {
            const tab = await chrome.tabs.create({ url: url, active: true });
            currentTabId = tab.id;
        }

        // 2. Wait for Load
        const waitForLoad = () => {
            return new Promise((resolve) => {
                let isResolved = false;
                
                // Fallback timeout in case page never finishes loading
                const timeoutId = setTimeout(() => {
                    if (!isResolved) {
                        isResolved = true;
                        chrome.tabs.onUpdated.removeListener(listener);
                        resolve();
                    }
                }, 10000); // Max 10s wait for nav

                const listener = (tabId, info, tab) => {
                    if (tabId === currentTabId && info.status === 'complete') {
                        if (!isResolved) {
                            isResolved = true;
                            clearTimeout(timeoutId);
                            chrome.tabs.onUpdated.removeListener(listener);
                            resolve();
                        }
                    }
                };

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
        };

        await waitForLoad();
        
        if (wait_ms) {
            await new Promise(r => setTimeout(r, wait_ms));
        } else {
            await new Promise(r => setTimeout(r, 4000));
        }

        // 3. Execute payload script dynamically using named functions (MV3 Compliant)
        if (type === "execute_named_function" && script) {
            const funcName = script; // e.g. "executeLiveSearch"
            const funcMap = {
                "executeLiveSearch": executeLiveSearch,
                "extractTrendlyneData": extractTrendlyneData,
                "executeTrendlyneSearch": executeTrendlyneSearch,
                "extractStockGroData": extractStockGroData
            };
            
            if (funcMap[funcName]) {
                const results = await chrome.scripting.executeScript({
                    target: { tabId: currentTabId },
                    func: funcMap[funcName],
                    args: job.args || []
                });
                await submitResult(job_id, results[0].result);
            } else {
                await submitResult(job_id, { error: `Function ${funcName} not found in extension.` });
            }
        } else {
            await submitResult(job_id, { error: `Unsupported job type: ${type}` });
        }
    } catch (e) {
        console.error("Script execution failed", e);
        await submitResult(job_id, { error: e.toString() });
    }
}

async function submitResult(job_id, data) {
    try {
        if (data && data.error) {
            setBadge('red'); 
        } else {
            setBadge('white');
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

// Start polling
pollForJobs();

// ── Perplexity Injected Functions ───────────────────────────────────

async function executeLiveSearch(query, usePro = false) {
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

                    // Close the "Your free searches will reset in a few hours" modal if it exists
                    const upgradeModals = Array.from(document.querySelectorAll('button')).filter(b => b.innerText.includes('Upgrade') || b.innerText.includes('Close') || b.getAttribute('aria-label') === 'Close');
                    upgradeModals.forEach(b => {
                        try { b.click(); } catch(e) {}
                    });

                    // Future-proofed search using Shadow DOM piercing just in case Perplexity switches architecture
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
                    if (usePro) {
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
                                console.log("Enabled Pro Search");
                            }
                        } catch (e) {
                            console.log("Could not toggle Pro Search", e);
                        }
                    } else {
                        // Turn OFF Pro search if it is accidentally checked!
                        try {
                            const allButtons = Array.from(document.querySelectorAll('button'));
                            const proToggle = allButtons.find(b => {
                                const isProText = (b.innerText || "").toLowerCase().includes('pro');
                                const parentText = (b.parentElement && b.parentElement.innerText || "").toLowerCase();
                                const isChecked = b.getAttribute('aria-checked') === 'true';
                                const isSwitch = b.getAttribute('role') === 'switch';
                                return (isProText && isChecked) || (isSwitch && isChecked && parentText.includes('pro'));
                            });
                            if (proToggle) {
                                proToggle.click();
                                console.log("Disabled Pro Search for speed/limits");
                            }
                        } catch (e) {
                            console.log("Could not disable Pro Search", e);
                        }
                    }

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
                                        answerText = Array.from(proseElements).map(el => el.textContent).join('\\n\\n');
                                    } else {
                                        const paragraphs = Array.from(document.querySelectorAll('main p, div[dir="auto"] p, .break-words p')).map(p => p.textContent).join('\\n');
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

// ── Trendlyne Injected Functions ───────────────────────────────────

async function executeTrendlyneSearch(ticker) {
    return new Promise((resolve) => {
        try {
            // Trendlyne's main search bar:
            const searchInput = document.querySelector('input[placeholder*="Search Stock"], input[name="q"], .tl-search-input');
            if (!searchInput) {
                resolve({ error: "Trendlyne search bar not found" });
                return;
            }
            
            // Type the ticker
            searchInput.focus();
            searchInput.value = "";
            document.execCommand('insertText', false, ticker);
            
            // Wait for dropdown
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
                    resolve({ success: true, clicked: found.innerText });
                } else {
                    const enterEvent = new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, bubbles: true });
                    searchInput.dispatchEvent(enterEvent);
                    resolve({ success: true, method: "enter_key" });
                }
            }, 2000);
        } catch(e) {
            resolve({ error: "executeTrendlyneSearch error: " + e.message });
        }
    });
}

function extractTrendlyneData() {
    try {
        const dvmScore = document.querySelector('.dvm-score, .score-container')?.innerText || "DVM Score not found";
        const metrics = Array.from(document.querySelectorAll('.metric-item, .alert-item')).map(m => m.innerText);
        
        // Sometimes the DVM is inside specific divs: 
        const durability = document.querySelector('div[title*="Durability"]')?.innerText || "N/A";
        const valuation = document.querySelector('div[title*="Valuation"]')?.innerText || "N/A";
        const momentum = document.querySelector('div[title*="Momentum"]')?.innerText || "N/A";

        // Try extracting any red/green alerts (e.g., volume shockers)
        const alerts = Array.from(document.querySelectorAll('.tl-alert, .technical-alert')).map(el => el.innerText);

        return {
            dvm_score_raw: dvmScore,
            durability: durability,
            valuation: valuation,
            momentum: momentum,
            alerts: alerts,
            metrics: metrics,
            url: window.location.href
        };
    } catch(e) {
        return { error: "extractTrendlyneData error: " + e.message };
    }
}

// ── StockGro Injected Functions ───────────────────────────────────
function extractStockGroData() {
    try {
        const data = {};
        data.url = window.location.href;
        data.pageTitle = document.title;
        
        // Extract links from nav to see what sections exist
        const navLinks = Array.from(document.querySelectorAll('a')).map(a => a.href);
        data.navLinks = [...new Set(navLinks)];
        
        // Extract all visible text blocks that might contain portfolio or expert names
        const textBlocks = Array.from(document.querySelectorAll('div, span, p, h1, h2, h3'))
            .filter(el => {
                const rect = el.getBoundingClientRect();
                return rect.width > 0 && rect.height > 0 && el.innerText && el.innerText.trim().length > 0;
            })
            .map(el => el.innerText.trim());
            
        data.visibleTextSample = [...new Set(textBlocks)].slice(0, 50); // first 50 unique text nodes
        
        return data;
    } catch(e) {
        return { error: "extractStockGroData error: " + e.message };
    }
}

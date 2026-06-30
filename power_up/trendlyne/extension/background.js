const SERVER_URL = "http://127.0.0.1:8787";
const POLL_INTERVAL_MS = 2000;

let isProcessing = false;

async function pollQueue() {
    if (isProcessing) return;

    try {
        let res = await fetch(`${SERVER_URL}/jobs/next`);
        if (res.status === 204) return;
        if (!res.ok) return;

        let data = await res.json();
        if (data && data.job) {
            console.log("[Trendlyne Bridge] Picked up job:", data.job);
            isProcessing = true;
            processJob(data.job);
        }
    } catch (e) {
        // Server probably offline
    }
}

async function processJob(job) {
    try {
        // 1. Ensure we have a Trendlyne tab
        let allTabs = await chrome.tabs.query({});
        let tabs = allTabs.filter(t => t.url && t.url.includes('trendlyne.com'));
        let tabId;
        if (tabs.length === 0) {
            console.log("[Trendlyne Bridge] No tab found, creating one...");
            let newTab = await chrome.tabs.create({url: 'https://trendlyne.com/'});
            tabId = newTab.id;
            await new Promise(r => setTimeout(r, 6000));
        } else {
            tabId = tabs[0].id;
            await chrome.tabs.update(tabId, {active: true});
        }

        // 2. Navigate to Trendlyne homepage to use the actual search bar
        let symbol = (job.ticker || job.query).split('.')[0]; // e.g. TCS.NS -> TCS
        await chrome.tabs.update(tabId, { url: 'https://trendlyne.com/', active: true });
        await new Promise(r => setTimeout(r, 8000)); // Wait for homepage to load
        
        let targetUrl = await new Promise((resolve) => {
            chrome.scripting.executeScript({
                target: { tabId: tabId },
                func: async (sym) => {
                    try {
                        let searchInput = document.getElementById('navbar-desktop-search') || document.querySelector('input[name="search"]');
                        if (!searchInput) return null;
                        
                        searchInput.focus();
                        searchInput.value = sym;
                        searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                        searchInput.dispatchEvent(new Event('change', { bubbles: true }));
                        searchInput.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: 'Enter' }));
                        
                        // Wait for the dropdown
                        for (let i = 0; i < 20; i++) {
                            await new Promise(r => setTimeout(r, 500));
                            // Look for the autocomplete links
                            let links = Array.from(document.querySelectorAll('a[href*="/equity/"]'));
                            for (let link of links) {
                                // Match the exact symbol if possible, or just the first equity link in the dropdown
                                if (link.href.toLowerCase().includes('/equity/') && !link.href.includes('marketmind')) {
                                    // Make sure it's visible or inside a dropdown container
                                    if (link.closest('.ui-autocomplete') || link.closest('ul') || link.offsetParent !== null) {
                                        return link.href;
                                    }
                                }
                            }
                        }
                        return null;
                    } catch (e) {
                        return null;
                    }
                },
                args: [symbol]
            }, (results) => {
                if (results && results[0] && results[0].result) resolve(results[0].result);
                else resolve(null);
            });
        });
        
        if (!targetUrl) throw new Error(`Could not find URL for ${symbol} using DOM search`);
        
        // 3. Navigate the tab to the found equity page
        await chrome.tabs.update(tabId, { url: targetUrl, active: true });
        await new Promise(r => setTimeout(r, 10000)); // Wait 10s for page load
        
        // 4. Extract data from the loaded page
        let response = await new Promise((resolve, reject) => {
            chrome.scripting.executeScript({
                target: { tabId: tabId },
                func: (sym) => {
                    function clean(text) { return (text || "").replace(/\s+/g, " ").trim(); }
                    try {
                        let rawText = clean(document.body.innerText).slice(0, 15000);
                        let tables = Array.from(document.querySelectorAll('table')).map(table => {
                            let headers = Array.from(table.querySelectorAll('th')).map(th => clean(th.innerText));
                            let rows = Array.from(table.querySelectorAll('tr')).map(tr => {
                                return Array.from(tr.querySelectorAll('td')).map(td => clean(td.innerText));
                            }).filter(r => r.length > 0);
                            return { headers, rows };
                        });
                        
                        let blocks = Array.from(document.querySelectorAll('div.card, div.panel, section')).map(s => clean(s.innerText));
                        let relevantBlocks = blocks.filter(b => b.toLowerCase().includes('delivery') || b.toLowerCase().includes('fii') || b.toLowerCase().includes('deal'));
                        
                        return {
                            text: `Trendlyne DOM Extract for ${sym}:\n\n` + relevantBlocks.join("\n\n---\n\n"),
                            tables: tables
                        };
                    } catch (e) {
                        return { error: e.toString() };
                    }
                },
                args: [symbol]
            }, (results) => {
                if (chrome.runtime.lastError) reject(chrome.runtime.lastError);
                else if (results && results[0] && results[0].result) resolve(results[0].result);
                else resolve({ text: "Empty response" });
            });
        });

        if (response && response.error) {
            throw new Error(response.error);
        }

        // Post result back
        await fetch(`${SERVER_URL}/jobs/${job.id}/result`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                result: response || { text: "Empty response" }
            })
        });

    } catch (e) {
        console.error("[Trendlyne Bridge] Job Failed:", e);
        await fetch(`${SERVER_URL}/jobs/${job.id}/result`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                result: { error: e.toString() }
            })
        });
    } finally {
        isProcessing = false;
    }
}

// Keep service worker alive
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "PING") {
        sendResponse({ status: "PONG" });
    }
});

// Start polling
setInterval(pollQueue, POLL_INTERVAL_MS);
console.log("[Trendlyne Bridge] Service Worker Started.");

// Keep service worker alive with alarms
chrome.alarms.create("keepAlive", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepAlive") {
    console.log("[Trendlyne Bridge] Alarm woke up Service Worker.");
    pollQueue();
  }
});

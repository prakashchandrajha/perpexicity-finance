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
        let allTabs = await chrome.tabs.query({});
        let tabs = allTabs.filter(t => t.url && t.url.includes('trendlyne.com/marketmind'));
        let tabId;
        if (tabs.length === 0) {
            console.log("[Trendlyne Bridge] No tab found, creating one...");
            let newTab = await chrome.tabs.create({url: 'https://trendlyne.com/marketmind/ask-ai/'});
            tabId = newTab.id;
            await new Promise(r => setTimeout(r, 6000)); // Wait for page to load
        } else {
            tabId = tabs[0].id;
            await chrome.tabs.update(tabId, {active: true});
        }

        // Make the tab active (Trendlyne might require window focus)
        let actualTab = await chrome.tabs.get(tabId);
        await chrome.tabs.update(tabId, { active: true });
        if (actualTab && actualTab.windowId) {
            await chrome.windows.update(actualTab.windowId, { focused: true });
        }

        // Send query via executeScript
        let response = await new Promise((resolve, reject) => {
            chrome.scripting.executeScript({
                target: { tabId: tabId },
                func: async (query) => {
                    async function wait(ms) { return new Promise(r => setTimeout(r, ms)); }
                    
                    console.log("[Trendlyne Bridge] Injecting query:", query);
                    await wait(1000); // Give the UI a second to settle in case of tab switch
                    
                    // Click Continue if on the selection screen
                    let btns = Array.from(document.querySelectorAll('button'));
                    let continueBtn = btns.find(b => b.innerText && b.innerText.toLowerCase().includes('continue'));
                    if (continueBtn) {
                        console.log("[Trendlyne Bridge] Found Continue button, clicking it...");
                        continueBtn.click();
                        await wait(1500);
                    }
                    
                    let textarea = document.querySelector('#search-text-area') || document.querySelector('textarea');
                    if (!textarea) {
                        return { error: "Could not find chat input field (#search-text-area) on Trendlyne page." };
                    }
                    
                    let container = document.getElementById('ai-agents-demo') || document.body;
                    let initialBotCount = document.querySelectorAll('.bot-content').length;
                    
                    textarea.value = query;
                    textarea.dispatchEvent(new Event('input', { bubbles: true }));
                    textarea.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    await wait(500);
                    let submitBtn = document.querySelector('button.searchBtn') || document.querySelector('button[type="submit"]');
                    if (submitBtn) {
                        submitBtn.click();
                    } else {
                        textarea.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
                    }
                    
                    console.log("[Trendlyne Bridge] Waiting for response stream...");
                    let responseText = "";
                    for (let i = 0; i < 45; i++) {
                        await wait(1000);
                        let botMessages = document.querySelectorAll('.bot-content');
                        if (botMessages.length > initialBotCount) {
                            let lastMsg = botMessages[botMessages.length - 1];
                            let currentLength = lastMsg.innerText.length;
                            
                            // Wait for streaming to finish inside this specific bot message
                            let previousLength = currentLength;
                            let stableCount = 0;
                            for(let j = 0; j < 30; j++) {
                                await wait(1000);
                                let newLength = lastMsg.innerText.length;
                                if (newLength > 10 && newLength === previousLength) {
                                    stableCount++;
                                    if (stableCount >= 2) {
                                        responseText = lastMsg.innerText.trim();
                                        break;
                                    }
                                } else {
                                    stableCount = 0;
                                    previousLength = newLength;
                                }
                            }
                            if (responseText) break;
                        }
                    }
                    
                    if (!responseText) {
                        return { error: "Timeout waiting for Trendlyne AI response." };
                    }
                    return { text: responseText };
                },
                args: [job.query]
            }, (results) => {
                if (chrome.runtime.lastError) {
                    reject(chrome.runtime.lastError);
                } else if (results && results[0] && results[0].result) {
                    resolve(results[0].result);
                } else {
                    resolve({ text: "Empty response" });
                }
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
                result: { text: response ? response.text : "Empty response" }
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

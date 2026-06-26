// content.js - Keep-Alive Heartbeat
// Injected into Perplexity tabs to keep the background Service Worker awake.

setInterval(() => {
    try {
        chrome.runtime.sendMessage({ type: "KEEP_ALIVE" });
    } catch (e) {
        // Ignored. Might happen if extension is reloaded but tab isn't.
    }
}, 20000); // 20 seconds

let keepAlive = setInterval(() => {
    chrome.runtime.sendMessage({ type: "PING" }, (res) => {
        if (chrome.runtime.lastError) {}
    });
}, 10000);

async function wait(ms) {
    return new Promise(r => setTimeout(r, ms));
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
    if (msg.type === "RUN_QUERY") {
        runChat(msg.query).then(text => {
            sendResponse({ text });
        }).catch(e => {
            sendResponse({ error: e.toString() });
        });
        return true; // async response
    }
});

async function runChat(query) {
    console.log("[Trendlyne Bridge] Injecting query:", query);

    // Find textarea or chat input
    let textarea = document.querySelector('#search-text-area');
    if (!textarea) {
        throw new Error("Could not find chat input field (#search-text-area) on Trendlyne page.");
    }

    // Capture the current number of chat messages to detect the new response
    let getMessages = () => document.querySelectorAll('.chat-message, .message, .bot-message');
    let initialCount = getMessages().length;

    // Type query
    textarea.value = query;
    textarea.dispatchEvent(new Event('input', { bubbles: true }));
    textarea.dispatchEvent(new Event('change', { bubbles: true }));

    await wait(500);

    // Find submit button (usually a button near textarea or an SVG send icon)
    let submitBtn = document.querySelector('button.searchBtn');
    
    if (submitBtn) {
        submitBtn.click();
    } else {
        // Fallback to Enter key
        textarea.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true }));
    }

    // Wait for response to stream
    console.log("[Trendlyne Bridge] Waiting for response...");
    let responseText = "";
    
    for (let i = 0; i < 45; i++) { // wait up to 45 seconds
        await wait(1000);
        let msgs = getMessages();
        if (msgs.length > initialCount) {
            let lastMsg = msgs[msgs.length - 1];
            // Check if it's still typing (many sites use a blinking cursor or loader class)
            let isTyping = lastMsg.innerText.includes('...') || lastMsg.querySelector('.typing, .loader');
            
            if (!isTyping && lastMsg.innerText.trim().length > 10) {
                // To be safe, wait 1 more second to ensure stream is totally finished
                await wait(1000); 
                responseText = msgs[msgs.length - 1].innerText;
                break;
            }
        }
    }

    if (!responseText) {
        // Fallback: just return all text if we couldn't isolate the last message cleanly
        throw new Error("Timeout waiting for Trendlyne AI response.");
    }

    console.log("[Trendlyne Bridge] Got response:", responseText.substring(0, 50) + "...");
    return responseText;
}

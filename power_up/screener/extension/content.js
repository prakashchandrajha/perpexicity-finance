setInterval(() => {
  chrome.runtime.sendMessage({ type: "PING" }).catch(() => {});
}, 10000);


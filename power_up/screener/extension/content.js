setInterval(() => {
  chrome.runtime.sendMessage({ ping: "keepAlive" }).catch(() => {});
}, 10000);

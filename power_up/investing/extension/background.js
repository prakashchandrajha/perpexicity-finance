const SERVER = "http://127.0.0.1:8788";
let busy = false;

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function postJson(url, payload) {
  await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

function extractInvestingPage(job) {
  function clean(text) {
    return (text || "").replace(/\s+/g, " ").trim();
  }

  const title = clean(document.title);
  
  // Extract summary consensus badge if present
  let consensus = "UNKNOWN";
  const badges = Array.from(document.querySelectorAll("span, div, a")).filter(el => {
    const txt = clean(el.innerText).toUpperCase();
    return ["STRONG BUY", "STRONG SELL", "BUY", "SELL", "NEUTRAL"].includes(txt) && el.children.length === 0;
  });
  if (badges.length > 0) {
    consensus = clean(badges[0].innerText).toUpperCase();
  }

  // Extract tables (Pivots, Technical Indicators, Moving Averages)
  const tables = Array.from(document.querySelectorAll("table")).map(t => {
    const headers = Array.from(t.querySelectorAll("thead th")).map(th => clean(th.innerText));
    const rows = Array.from(t.querySelectorAll("tbody tr")).map(tr => {
      return Array.from(tr.querySelectorAll("td")).map(td => clean(td.innerText));
    });
    return { headers, rows };
  });

  // Extract main text summary
  let mainText = "";
  const mainDiv = document.querySelector("main") || document.querySelector("#contentSection") || document.body;
  if (mainDiv) {
    mainText = clean(mainDiv.innerText).slice(0, 3500);
  }

  return {
    job_id: job.id,
    url: job.url,
    title: title,
    consensus: consensus,
    tables: tables.slice(0, 5),
    text_snippet: mainText,
    captured_at: new Date().toISOString()
  };
}

async function handleJob(job) {
  busy = true;
  try {
    let tabs = await chrome.tabs.query({ url: "*://*.investing.com/*" });
    let tabId = null;
    if (tabs.length > 0) {
      tabId = tabs[0].id;
      await chrome.tabs.update(tabId, { url: job.url, active: true });
    } else {
      let newTab = await chrome.tabs.create({ url: job.url, active: true });
      tabId = newTab.id;
    }

    await sleep(7000); // Wait for Cloudflare and dynamic table loading

    const [res] = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: extractInvestingPage,
      args: [job],
    });

    if (res && res.result) {
      await postJson(`${SERVER}/jobs/${job.id}/result`, { result: res.result });
    } else {
      await postJson(`${SERVER}/jobs/${job.id}/result`, {
        result: { error: "Failed to extract script from Investing.com" },
      });
    }
  } catch (err) {
    await postJson(`${SERVER}/jobs/${job.id}/result`, {
      result: { error: String(err) },
    });
  } finally {
    busy = false;
  }
}

async function poll() {
  if (busy) return;
  try {
    const r = await fetch(`${SERVER}/jobs/next`);
    if (r.status === 200) {
      const data = await r.json();
      if (data && data.job) {
        await handleJob(data.job);
      }
    }
  } catch (e) {
    // Server offline or unreachable
  }
}

// Chrome Alarms API keeps the service worker alive and wakes it up
chrome.alarms.create("investing-poll", { periodInMinutes: 0.05 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "investing-poll") { poll(); }
});

setInterval(poll, 2000);
poll();
console.log("[Investing Bridge] Service worker started.");

const SERVER = "http://127.0.0.1:8776";
const SCREENER = "https://www.screener.in";
const POLL_MS = 2000;

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

function buildUrl(job) {
  if (job.job_type === "company") {
    return `${SCREENER}/company/${encodeURIComponent(job.symbol)}/consolidated/`;
  }
  const query = encodeURIComponent(job.query || "");
  return `${SCREENER}/screen/raw/?query=${query}`;
}

function extractScreenerPage(job) {
  function clean(text) {
    return (text || "").replace(/\s+/g, " ").trim();
  }

  const tables = Array.from(document.querySelectorAll("table")).map((table, index) => {
    const headers = Array.from(table.querySelectorAll("thead th")).map((th) => clean(th.innerText));
    const fallbackHeaders = Array.from(table.querySelectorAll("tr:first-child th, tr:first-child td")).map((cell) => clean(cell.innerText));
    const finalHeaders = headers.length ? headers : fallbackHeaders;
    const bodyRows = Array.from(table.querySelectorAll("tbody tr"));
    const rows = bodyRows.map((tr) => {
      const cells = Array.from(tr.querySelectorAll("td, th")).map((td) => clean(td.innerText));
      const row = {};
      cells.forEach((value, cellIndex) => {
        const key = finalHeaders[cellIndex] || `col_${cellIndex + 1}`;
        row[key] = value;
      });
      const firstLink = tr.querySelector("a[href*='/company/']");
      if (firstLink) {
        row._href = firstLink.getAttribute("href");
      }
      return row;
    }).filter((row) => Object.values(row).some(Boolean));
    const heading = clean(table.closest("section")?.querySelector("h2, h3")?.innerText || "");
    return { index, heading, headers: finalHeaders, rows };
  });

  const ratios = {};
  const allowedRatioNames = [
    "Market Cap", "Current Price", "Stock P/E", "Book Value", "Dividend Yield",
    "ROCE", "ROE", "Face Value", "High / Low", "Debt to equity",
    "Promoter holding", "Pledged percentage", "Interest Coverage Ratio"
  ];
  const ratioItems = Array.from(document.querySelectorAll("#top-ratios li, .company-ratios li"));
  ratioItems.forEach((li) => {
    const text = clean(li.innerText);
    const matchedName = allowedRatioNames.find((name) => text.toLowerCase().startsWith(name.toLowerCase()));
    if (!matchedName) return;
    const value = clean(text.slice(matchedName.length));
    if (value && value.length < 60) {
      ratios[matchedName] = value;
    }
  });
  return {
    job_id: job.id,
    job_type: job.job_type,
    url: location.href,
    title: clean(document.querySelector("h1")?.innerText || document.title),
    captured_at: new Date().toISOString(),
    tables,
    ratios,
    raw_text: clean(document.body.innerText).slice(0, 20000),
    error: null,
  };
}

async function runJob(job) {
  const url = buildUrl(job);
  let allTabs = await chrome.tabs.query({});
  let screenerTabs = allTabs.filter(t => t.url && t.url.includes('screener.in'));
  let targetTab;
  if (screenerTabs.length === 0) {
      console.log("[Screener Bridge] No tab found, creating one...");
      targetTab = await chrome.tabs.create({url: 'https://www.screener.in/'});
      await sleep(6000); // Wait for page to load
  } else {
      targetTab = screenerTabs[0];
      await chrome.tabs.update(targetTab.id, {active: true});
  }
  
  let tabId = targetTab.id;
  try {
    await chrome.tabs.update(tabId, { url });
    await sleep(7000);
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tabId },
      func: extractScreenerPage,
      args: [job],
    });
    await postJson(`${SERVER}/jobs/${job.id}/result`, { result: result.result });
  } catch (error) {
    await postJson(`${SERVER}/jobs/${job.id}/result`, {
      result: {
        job_id: job.id,
        job_type: job.job_type,
        url,
        captured_at: new Date().toISOString(),
        tables: [],
        ratios: {},
        raw_text: "",
        error: String(error),
      },
    });
  } finally {
    // Keep the user's Screener tab alive for session continuity and future jobs.
  }
}
async function poll() {
  if (busy) return;
  try {
    const response = await fetch(`${SERVER}/jobs/next`);
    if (response.status !== 200) return;
    const payload = await response.json();
    if (!payload.job) return;
    if (payload.job.job_type === "reload_extension" || payload.job.type === "reload_extension") {
      console.log("[Screener Bridge] Reloading extension via command from UI!");
      try { await postJson(`${SERVER}/jobs/${payload.job.id}/result`, { result: { status: "reloaded" } }); } catch(e){}
      setTimeout(() => chrome.runtime.reload(), 500);
      return;
    }
    busy = true;
    await runJob(payload.job);
  } catch (_error) {
    // Server may be offline. Poll quietly.
  } finally {
    busy = false;
  }
}

setInterval(poll, POLL_MS);
poll();

// Keep-alive heartbeat listener
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "PING" || msg.ping === "keepAlive") {
    sendResponse({ status: "PONG" });
  }
});

console.log("[Screener Bridge] Service Worker Started.");

// Keep service worker alive with alarms
chrome.alarms.create("keepAlive", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepAlive") {
    console.log("[Screener Bridge] Alarm woke up Service Worker.");
    poll();
  }
});



const SERVER = "http://127.0.0.1:8777";
const CHARTINK = "https://chartink.com";
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

function extractChartinkPage(job) {
  function clean(text) {
    return (text || "").replace(/\s+/g, " ").trim();
  }

  // Chartink results are in a table inside #DataTables_Table_0 or table.table-striped
  // The first table on the page is usually the scanner query criteria. We want the results table.
  const tables = Array.from(document.querySelectorAll("table"));
  let table = null;
  for (const t of tables) {
    if (t.innerText.includes("Stock Name") || t.innerText.includes("Symbol") || t.id.includes("DataTables")) {
      table = t;
      break;
    }
  }
  
  if (!table) {
    return {
      job_id: job.id,
      scanner_name: job.scanner_name,
      captured_at: new Date().toISOString(),
      stocks: [],
      raw_tables: [],
      error: "No table found on Chartink page",
    };
  }

  const headers = Array.from(table.querySelectorAll("thead th")).map(th => clean(th.innerText));
  const bodyRows = Array.from(table.querySelectorAll("tbody tr"));
  
  const stocks = [];
  const raw_rows = [];

  bodyRows.forEach((tr) => {
    const cells = Array.from(tr.querySelectorAll("td"));
    if (!cells.length) return;

    const rowData = {};
    headers.forEach((h, i) => {
      rowData[h] = clean(cells[i]?.innerText);
    });
    raw_rows.push(rowData);

    // Chartink typically has columns like "Symbol", "Stock Name", "Close", "Volume", "% Chg"
    // We try to find them fuzzily
    let symbol = "";
    let name = "";
    let price = 0;
    let volume = 0;
    let change_pct = 0;

    for (let i = 0; i < headers.length; i++) {
      const h = headers[i].toLowerCase();
      const val = clean(cells[i]?.innerText);
      if (h.includes("symbol") || h === "nsecode") symbol = val;
      else if (h.includes("name") || h.includes("company")) name = val;
      else if (h.includes("close") || h.includes("price") || h.includes("ltp")) price = parseFloat(val.replace(/,/g, "")) || 0;
      else if (h.includes("vol")) volume = parseFloat(val.replace(/,/g, "")) || 0;
      else if (h.includes("% chg") || h.includes("change")) change_pct = parseFloat(val.replace(/,/g, "").replace("%", "")) || 0;
    }

    // fallback if no exact header match but typical structure: 
    // SR, Stock Name, Symbol, Links, % Chg, Price, Vol
    if (!symbol && cells.length > 2) {
        // Just extract all as metrics
    }

    if (symbol) {
        stocks.push({
            symbol: symbol,
            name: name,
            price: price,
            volume: volume,
            change_pct: change_pct,
            metrics: rowData
        });
    }
  });

  return {
    job_id: job.id,
    scanner_name: job.scanner_name,
    captured_at: new Date().toISOString(),
    stocks: stocks,
    raw_tables: [{ headers, rows: raw_rows }],
    error: null,
  };
}

async function runJob(job) {
  let allTabs = await chrome.tabs.query({});
  let chartinkTabs = allTabs.filter(t => t.url && t.url.includes('chartink.com'));
  let targetTab;
  if (chartinkTabs.length === 0) {
      console.log("[Chartink Bridge] No tab found, creating one...");
      targetTab = await chrome.tabs.create({url: 'https://chartink.com/'});
      await sleep(6000); // Wait for page to load
  } else {
      targetTab = chartinkTabs[0];
      await chrome.tabs.update(targetTab.id, {active: true});
  }
  
  let tabId = targetTab.id;
  try {
    await chrome.tabs.update(tabId, { url: job.url });
    await sleep(7000); // give time to load page

    // Execute script to click 'Run Scan' if needed
    await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        const runBtn = document.querySelector("#run_scan");
        if (runBtn) runBtn.click();
      }
    });
    
    // Wait for datatable to populate
    await sleep(6000);

    const [injection] = await chrome.scripting.executeScript({
      target: { tabId },
      func: extractChartinkPage,
      args: [job],
    });

    const result = injection.result;
    console.log("[Chartink Bridge] Extraction complete:", result);
    await postJson(`${SERVER}/complete`, result);

  } catch (err) {
    console.error("[Chartink Bridge] Error processing job", err);
    await postJson(`${SERVER}/complete`, {
      job_id: job.id,
      scanner_name: job.scanner_name,
      error: err.toString(),
    });
  }
}

async function pollQueue() {
  if (busy) return;
  busy = true;
  try {
    const res = await fetch(`${SERVER}/queue`);
    if (res.ok) {
      const job = await res.json();
      if (job && job.id) {
        if (job.type === "reload_extension" || job.scanner_name === "RELOAD") {
          console.log("[Chartink Bridge] Reloading extension via command from UI!");
          try { await postJson(`${SERVER}/complete`, { job_id: job.id, scanner_name: "RELOAD", captured_at: new Date().toISOString(), stocks: [], raw_tables: [], error: null }); } catch(e){}
          setTimeout(() => chrome.runtime.reload(), 500);
          return;
        }
        console.log("[Chartink Bridge] Received job:", job);
        await runJob(job);
      }
    }
  } catch (err) {
    // server down
  } finally {
    busy = false;
  }
}

setInterval(pollQueue, POLL_MS);
pollQueue();
console.log("[Chartink Bridge] Service worker started.");

// Keep service worker alive with alarms (MV3 kills workers after 30s idle)
chrome.alarms.create("keepAlive", { periodInMinutes: 0.4 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepAlive") {
    console.log("[Chartink Bridge] Alarm woke up Service Worker.");
    pollQueue();
  }
});

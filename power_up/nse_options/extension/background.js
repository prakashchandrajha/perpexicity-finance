const SERVER = "http://127.0.0.1:8778";

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

async function runJob(job) {
  let allTabs = await chrome.tabs.query({});
  let nseTabs = allTabs.filter(t => t.url && t.url.includes('nseindia.com'));
  let targetTab;
  
  if (nseTabs.length === 0) {
      console.log("[NSE Bridge] No NSE tab found, creating one...");
      targetTab = await chrome.tabs.create({url: 'https://www.nseindia.com/option-chain'});
      await sleep(10000);
  } else {
      targetTab = nseTabs[0];
      if (!targetTab.url.includes('option-chain')) {
        await chrome.tabs.update(targetTab.id, {url: 'https://www.nseindia.com/option-chain'});
        await sleep(8000);
      }
  }
  
  let tabId = targetTab.id;
  try {
    // If equity, select in the symbol dropdown; if index, select in the index dropdown
    if (!job.is_index) {
      await chrome.scripting.executeScript({
        target: { tabId },
        world: "MAIN",
        func: (symbol) => {
          const sel = document.getElementById('select_symbol');
          if (sel) { sel.value = symbol; sel.dispatchEvent(new Event('change', { bubbles: true })); }
        },
        args: [job.symbol],
      });
      await sleep(5000);
    } else {
      await chrome.scripting.executeScript({
        target: { tabId },
        world: "MAIN",
        func: (symbol) => {
          const sel = document.getElementById('equity_optionchain_select');
          if (sel) { sel.value = symbol; sel.dispatchEvent(new Event('change', { bubbles: true })); }
        },
        args: [job.symbol],
      });
      await sleep(5000);
    }

    // Set up isolated world listener for cross-world messaging
    await chrome.scripting.executeScript({
      target: { tabId },
      func: () => {
        window.__nse_result__ = null;
        window.addEventListener("message", (e) => {
          if (e.data && e.data.__nse_bridge__) {
            window.__nse_result__ = e.data.payload;
          }
        });
      },
    });

    // Scrape the DOM table in MAIN world
    await chrome.scripting.executeScript({
      target: { tabId },
      world: "MAIN",
      func: (symbol) => {
        function sendResult(payload) {
          window.postMessage({ __nse_bridge__: true, payload: payload }, "*");
        }
        
        try {
          // Get underlying price
          let underlying = 0;
          const bodyText = document.body.innerText;
          const m = bodyText.match(/Underlying\s+(?:Index\s*:\s*)?(?:[A-Z\s]+)\s+([\d,]+\.?\d*)/i);
          if (m) underlying = parseFloat(m[1].replace(/,/g, ''));
          
          // Get selected expiry
          const expirySelect = document.getElementById('expirySelect');
          const currentExpiry = expirySelect ? expirySelect.value : "unknown";
          
          // NSE table structure (confirmed via DOM inspection):
          // 21 cells per data row:
          // [0]  CE OI
          // [1]  CE CHG IN OI
          // [2]  CE VOLUME
          // [3]  CE IV
          // [4]  CE LTP (has <a> link)
          // [5]  CE CHG
          // [6]  CE BID QTY
          // [7]  CE BID
          // [8]  CE ASK
          // [9]  CE ASK QTY
          // [10] STRIKE (has <a href="javascript:;">)
          // [11] PE BID QTY
          // [12] PE BID
          // [13] PE ASK
          // [14] PE ASK QTY
          // [15] PE CHG
          // 23 cells per data row (including 2 chart columns)
          
          // Find all tr elements
          const allRows = document.querySelectorAll("table tr");
          
          let total_ce_oi = 0, total_pe_oi = 0;
          let max_ce_oi = 0, max_ce_strike = 0;
          let max_pe_oi = 0, max_pe_strike = 0;
          let rowCount = 0;
          
          for (const row of allRows) {
            const cells = Array.from(row.querySelectorAll("td"));
            if (cells.length !== 23) continue; // Data rows have exactly 23 cells (including 2 chart columns)
            
            // Strike is cell 11, it has an <a> with href="javascript:;"
            const strikeLink = cells[11].querySelector("a");
            if (!strikeLink) continue;
            
            const strikeText = strikeLink.innerText.trim().replace(/,/g, "");
            const strike = parseFloat(strikeText) || 0;
            if (strike === 0) continue;
            
            // CE OI = cell 1, PE OI = cell 21
            const ceOiText = cells[1].innerText.trim().replace(/,/g, "").replace(/-/g, "0");
            const peOiText = cells[21].innerText.trim().replace(/,/g, "").replace(/-/g, "0");
            
            const ce_oi = parseFloat(ceOiText) || 0;
            const pe_oi = parseFloat(peOiText) || 0;
            
            total_ce_oi += ce_oi;
            total_pe_oi += pe_oi;
            
            if (ce_oi > max_ce_oi) { max_ce_oi = ce_oi; max_ce_strike = strike; }
            if (pe_oi > max_pe_oi) { max_pe_oi = pe_oi; max_pe_strike = strike; }
            rowCount++;
          }
          
          if (rowCount === 0) {
            sendResult({ error: "Could not parse any rows. Found " + allRows.length + " tr elements total." });
            return;
          }
          
          const pcr = total_ce_oi > 0 ? Number((total_pe_oi / total_ce_oi).toFixed(3)) : 0;
          
          sendResult({
            source: "dom",
            symbol: symbol,
            underlying_price: underlying,
            current_expiry: currentExpiry,
            total_call_oi: total_ce_oi,
            total_put_oi: total_pe_oi,
            pcr: pcr,
            max_call_oi_strike: max_ce_strike,
            max_put_oi_strike: max_pe_strike,
            resistance_level: max_ce_strike,
            support_level: max_pe_strike,
            sentiment: pcr >= 1.0 ? "BULLISH" : "BEARISH",
            rows_parsed: rowCount,
          });
          
        } catch (err) {
          sendResult({ error: err.toString() });
        }
      },
      args: [job.symbol],
    });

    // Poll for result
    let result = null;
    for (let i = 0; i < 10; i++) {
      await sleep(1000);
      const [readResult] = await chrome.scripting.executeScript({
        target: { tabId },
        func: () => window.__nse_result__,
      });
      if (readResult.result) {
        result = readResult.result;
        break;
      }
    }
    
    if (!result) {
      throw new Error("No result received from DOM scraper after 10s");
    }
    
    if (result.error) {
      throw new Error(result.error);
    }
    
    console.log(`[NSE Bridge] ${job.symbol}: PCR=${result.pcr} Resistance=${result.resistance_level} Support=${result.support_level} (${result.rows_parsed} strikes)`);
    await postJson(`${SERVER}/complete`, {
        job_id: job.id,
        symbol: job.symbol,
        captured_at: new Date().toISOString(),
        raw_data: result,
        error: null
    });

  } catch (err) {
    console.error("[NSE Bridge] Error:", err);
    await postJson(`${SERVER}/complete`, {
      job_id: job.id,
      symbol: job.symbol,
      captured_at: new Date().toISOString(),
      raw_data: {},
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
        if (job.type === "reload_extension" || job.job_type === "reload_extension") {
          console.log("[NSE Bridge] Reloading extension via command from UI!");
          try { await postJson(`${SERVER}/complete`, { job_id: job.id, symbol: "RELOAD", captured_at: new Date().toISOString(), raw_data: { status: "reloaded" }, error: null }); } catch(e){}
          setTimeout(() => chrome.runtime.reload(), 500);
          return;
        }
        console.log("[NSE Bridge] Received job:", job);
        await runJob(job);
      }
    }
  } catch (err) {
    // server down
  } finally {
    busy = false;
  }
}

// Chrome Alarms API keeps the service worker alive
chrome.alarms.create("nse-poll", { periodInMinutes: 0.05 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "nse-poll") { pollQueue(); }
});

pollQueue();
console.log("[NSE Bridge] Service worker started (DOM scraper mode).");

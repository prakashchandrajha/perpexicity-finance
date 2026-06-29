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
  document.querySelectorAll("#top-ratios li, .company-ratios li, li").forEach((li) => {
    const text = clean(li.innerText);
    const match = text.match(/^(.+?)\s+(-?[\d,.]+%?|[\d,.]+ Cr\.?|.+)$/);
    if (match && text.length < 80) {
      ratios[clean(match[1])] = clean(match[2]);
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
  const tab = await chrome.tabs.create({ url, active: false });
  try {
    await sleep(7000);
    const [result] = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
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
    if (tab.id) {
      chrome.tabs.remove(tab.id);
    }
  }
}

async function poll() {
  if (busy) return;
  try {
    const response = await fetch(`${SERVER}/jobs/next`);
    if (response.status !== 200) return;
    const payload = await response.json();
    if (!payload.job) return;
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

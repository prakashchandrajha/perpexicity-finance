# Perplexity Finance Scraper — "The Ghost Extension" Architecture

## 📖 Overview

This project is a **dedicated data extraction layer** that scrapes financial intelligence and live market sentiment exclusively from [Perplexity AI Finance](https://www.perplexity.ai/finance). 

Its single job is to act as an automated AI Research Analyst: it asks Perplexity complex financial questions about stock tickers, extracts the conversational response, parses it into structured JSON trading signals (Sentiment, Trend, Catalysts, Urgency), and saves it for downstream algorithmic trading bots to consume.

### 🚫 What it does NOT do:
- Connect to Zerodha, AliceBlue, or any broker.
- Pull OHLCV charts from Yahoo Finance.
- Execute trades.
- This is strictly a **qualitative data extraction layer**.

---

## 🏗️ The "Ghost Extension" Architecture (Bypassing Cloudflare)

Previously, scraping Perplexity with headless browsers (Playwright, Selenium, Camoufox) resulted in instant IP bans and 16-second Cloudflare Turnstile blocks. 

This project solves that by shifting the paradigm to a **Local Server + Chrome Extension Bridge**:

1. **The Python Server (Producer)**: Python runs locally on port `8765`. It generates queries (e.g., "Why is RELIANCE moving today?") and places them in a local queue.
2. **The Chrome Extension (Consumer)**: A lightweight extension installed in your normal, logged-in Google Chrome browser polls the Python server every 2 seconds. 
3. **Execution**: When the extension sees a job, it opens a Perplexity tab, uses a "Holy Grail" injection technique (`document.execCommand`) to natively simulate human typing, bypasses React's event blockers, avoids Voice mode overlays, and perfectly captures the streaming AI response.
4. **Delivery**: The extension POSTs the extracted text back to Python, which parses it into JSON.

Because the queries execute inside your real browser profile where you are already logged in, Cloudflare sees you as a 100% legitimate human user.

---

## ⚙️ Installation & Setup

### Step 1: Install Python Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Install the Chrome Extension
1. Open Google Chrome and navigate to `chrome://extensions/`
2. Turn on **Developer Mode** (top right corner).
3. Click **Load unpacked** (top left).
4. Select the `extension/` folder located inside this project (`perplexity-finance-scraper/extension`).
5. **Pin the extension** to your toolbar so you can see the Traffic Light status badge.

### Step 3: Keep-Alive Precaution
Due to Chrome Manifest V3 rules, background extensions suspend after 30 seconds of inactivity. 
To prevent this, the extension utilizes a "Heartbeat". **Simply keep one Perplexity.ai tab open anywhere in your Chrome browser.** The extension will inject a silent heartbeat script into that tab, keeping the scraper queue awake 24/7.

---

## 🚦 Extension Traffic Light System

Look at the extension icon in your Chrome toolbar to know exactly what the system is doing:

- ⬜ **IDLE (White/Gray)**: The script is sleeping. The Python queue is empty, or the Python script isn't running.
- 🟩 **RUN (Green)**: The extension grabbed a job from Python and is actively scraping Perplexity.
- 🟥 **ERR (Red)**: A catastrophic failure occurred (e.g., Perplexity radically changed their UI, or the 120-second timeout was hit).

---

## 🚀 Usage

Run the Python script from the terminal to queue jobs for the extension to process.

**Run a Pre-Market analysis:**
```bash
./venv/bin/python main.py RELIANCE.NS --phase pre_market
```

**Run a Live-Market narrative check:**
```bash
./venv/bin/python main.py RELIANCE.NS --phase live_market
```

**Run a Post-Market recap:**
```bash
./venv/bin/python main.py RELIANCE.NS --phase post_market
```

---

## 📄 Output Data (JSON)

The output is saved in `data/YYYY-MM-DD/{phase}_{ticker}_{time}.json`. 
Your trading bot can read these files to make algorithmic decisions.

**Example output:**
```json
{
  "ticker": "RELIANCE.NS",
  "phase": "live_market",
  "timestamp": "2026-06-26T19:59:51.922332+00:00",
  "signals": {
    "sentiment_score": 5,
    "trend_direction": "BULLISH",
    "catalyst_tags": ["IPO", "EARNINGS", "TECH_AI"],
    "urgency": "BREAKING",
    "confidence": 0.8
  },
  "live_catalyst_narrative": "Reliance is moving on a mix of stock-specific headline flow..."
}
```

## 🛡️ Future-Proofing (Shadow DOM)

If Perplexity's engineers redesign their website and hide the search bar inside Web Components (Shadow DOM) to block scrapers, this extension includes a recursive **Shadow DOM piercing algorithm** that will automatically drill through the encrypted DOM layers to locate the input field and execute the trade query without failing.
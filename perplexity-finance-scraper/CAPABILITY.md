# Perplexity Finance Scraper — Core Capabilities

This project is a highly specialized "Why Engine." It ignores generic numerical data that brokers provide and strictly focuses on what only Perplexity AI can deliver: contextual, predictive, and causal narratives.

Here is exactly what this project is capable of extracting and delivering to your trading bot:

### 1. 🧠 AI-Synthesized Market Narratives
- It extracts the **causal chain** behind market moves, aggregating data from multiple news sources into a single, cohesive story.
- Example: Instead of just noting that a stock is down 20%, it explains *why* (e.g., "Pricing hike → memory cost inflation → supplier surge").

### 2. 🔀 "Double Cross" Correlation Engine
- Using the Master Intraday Prompt, the scraper can process complex "double cross" questions injected dynamically by your trading bot.
- **Capability:** If your bot detects a divergence (e.g., "Crude is up 3%, Reliance is flat, but HPCL is up 2%"), the scraper forces Perplexity to explicitly explain why the assets are diverging and what is suppressing the laggard.

### 3. 🌍 Global-to-India Translation
- The system asks Perplexity to contextualize global macro events (e.g., US consumer inflation data, KOSPI tech rout) and directly link them to specific Indian sectors or adjacent stocks.

### 4. 🚨 Dynamic Urgency & Catalyst Tagging
- Parses the AI narrative using NLP (Vader Sentiment + Regex) to classify the **Urgency** of the event (e.g., `BREAKING`, `BACKGROUND`).
- Automatically tags the precise **Catalysts** driving the action (e.g., `FII`, `EARNINGS`, `CRUDE`, `IPO`, `BLOCK_DEAL`).

### 5. 📉 Bear vs. Bull Key Issues Extraction
- Extracts Perplexity’s unique "Key Issues" panel during pre-market prep, providing structured arguments for both the Bull thesis and the Bear thesis for the upcoming trading day.

### 6. 🕒 Sentiment Drift Tracking
- The `sentiment_check` module queries the local SQLite database to calculate the historical sentiment delta (e.g., "Sentiment shifted from +2 to -5 over the last 4 hours") without needing to ping the Perplexity server.
- Allows your bot to instantly identify trend reversals before execution.

### 7. 🛡️ Anti-Block "Ghost" Architecture
- **Capability:** Bypasses all of Cloudflare's bot-protection and CAPTCHAs by using a specialized Chrome Extension that proxies requests through your actual, active, logged-in browser session. 
- Features built-in human-like React hydration delays and sequential watchlist pacing to ensure your account is never flagged for spam.

# COPILOT INSTRUCTION FILE
# Read this entire file first, then build the project top to bottom.
# Do not ask questions. Do not skip any file. Build everything listed here.

---

## WHAT THIS PROJECT DOES

User types a question like:
"Should I buy Reliance Industries stock this week?"

The script:
1. Opens Perplexity Finance in a browser
2. Types that question in the search box
3. Waits for the full answer to load
4. Scrapes the answer
5. Saves it as a clean JSON file on disk

That is it. Nothing else. No trading bot. No API. Just question → answer → JSON file saved.

---

## TECH STACK

- Python 3.11+
- Playwright (browser automation)
- Trafilatura (text extraction)
- Pydantic v2 (data validation)
- Loguru (logging)

---

## FOLDER STRUCTURE TO CREATE

```
perplexity-finance-scraper/
├── main.py
├── config.py
├── requirements.txt
├── scraper/
│   ├── __init__.py
│   ├── browser.py
│   └── extractor.py
├── models/
│   ├── __init__.py
│   └── schema.py
├── storage/
│   ├── __init__.py
│   └── save.py
└── data/
    └── .gitkeep
```

---

## FILE 1 — requirements.txt

```
playwright
trafilatura
pydantic
loguru
beautifulsoup4
aiofiles
```

---

## FILE 2 — config.py

```python
# All project settings live here. Never hardcode these anywhere else.

PERPLEXITY_URL = "https://www.perplexity.ai/finance"

# Where all JSON answer files get saved
DATA_DIR = "data"

# Browser settings
HEADLESS = True           # Set False to watch browser open (useful for debugging)
PAGE_TIMEOUT = 30000      # 30 seconds max to load page
ANSWER_TIMEOUT = 25000    # 25 seconds max to wait for answer

# How long to wait after answer appears before scraping
# Perplexity streams its answer — if you scrape too early you get half an answer
STREAM_WAIT_SECONDS = 4
```

---

## FILE 3 — models/schema.py

```python
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FinanceAnswer(BaseModel):
    # The exact question the user typed
    query: str

    # The full cleaned answer text from Perplexity
    answer_text: str

    # Stock tickers found in the answer e.g. ["RELIANCE", "TCS"]
    tickers_mentioned: list[str]

    # Source URLs Perplexity cited
    citations: list[str]

    # When the query was run
    query_timestamp: str

    # How many words in the answer
    word_count: int

    # True if we got a real answer, False if extraction failed
    extraction_success: bool

    # Always "https://www.perplexity.ai/finance"
    source_url: str
```

---

## FILE 4 — scraper/browser.py

Build an async class called `PerplexityBrowser`.

Rules:
- Use `async with PerplexityBrowser() as browser:` pattern
- Launch Chromium using config.HEADLESS setting
- Set this user agent on the browser context:
  `"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"`

Method: `async def get_answer_html(self, query: str) -> str`

Step by step what this method must do:
1. Go to config.PERPLEXITY_URL
2. Wait for network to be idle (networkidle)
3. Find the search box. Try these selectors IN ORDER, use first one that works:
   - `textarea[placeholder*="Ask"]`
   - `div[role="textbox"]`
   - `input[type="text"]`
4. Click the search box
5. Type the query with 60ms delay between characters (looks human)
6. Press Enter
7. Wait for the answer block to appear. Try these selectors IN ORDER:
   - `div.prose`
   - `div[class*="answer"]`
   - `div[class*="markdown"]`
   - `div[class*="response"]`
   Use page.wait_for_selector() with timeout = config.ANSWER_TIMEOUT
8. Sleep for config.STREAM_WAIT_SECONDS (answer is streaming, wait for it to finish)
9. Return full page HTML as string: `await page.content()`

If anything fails, log the error with loguru and raise an exception called `BrowserError`.
Define `BrowserError` at the top of this file.

```

---

## FILE 5 — scraper/extractor.py

Build a class called `FinanceExtractor`.

### Method 1: `extract_answer(self, html: str) -> str`

- Try trafilatura first:
  ```python
  text = trafilatura.extract(html, include_links=False, include_images=False)
  ```
- If trafilatura returns None or empty, fallback to BeautifulSoup:
  - Find all tags where class contains "prose", "answer", "markdown", "response"
  - Get their text with `.get_text(separator=" ", strip=True)`
- Clean the result:
  - Collapse multiple spaces into one
  - Collapse more than 2 newlines into 2
  - Strip whitespace from start and end
- Return cleaned string. If still empty, return `""`

### Method 2: `extract_citations(self, html: str) -> list[str]`

- Use BeautifulSoup
- Find all `<a>` tags
- Return unique href values that start with "http"
- Max 10 results

### Method 3: `extract_tickers(self, text: str) -> list[str]`

- Use regex pattern: `r'\b([A-Z]{1,5})\b'`
- Remove these common false positives:
  ```python
  IGNORE = {"I", "A", "AT", "BE", "DO", "GO", "IN", "IS", "IT", "ME",
            "MY", "NO", "OF", "ON", "OR", "SO", "TO", "US", "WE",
            "AND", "FOR", "THE", "ARE", "HAS", "NOT", "BUT", "ALL",
            "NEW", "NOW", "GET", "USE", "ITS"}
  ```
- Return unique list of remaining matches

---

## FILE 6 — storage/save.py

Build a class called `JsonStore`.

### Method: `async def save(self, answer: FinanceAnswer) -> str`

- Build filename from the query:
  - Lowercase the query
  - Replace spaces with underscores
  - Remove all characters that are not letters, numbers, or underscores
  - Trim to max 60 characters
  - Add timestamp prefix: `"20240115_143022_"`
  - Add `.json` extension
  - Example: `"20240115_143022_should_i_buy_reliance_industries_stock.json"`
- Create config.DATA_DIR folder if it does not exist
- Write the JSON file with `indent=2` so it is human readable
- Log the full file path with loguru
- Return the full file path as string

---

## FILE 7 — main.py

This is the entry point. The user runs this file.

```python
# HOW TO RUN:
# python main.py "Should I buy Reliance Industries stock this week?"
# python main.py "What is the outlook for NIFTY 50 this month?"
# python main.py "Is TCS a good buy right now?"
```

Steps main.py must do:
1. Read the question from sys.argv[1]
   - If no argument given, print usage instructions and exit
2. Log: `"Question: {query}"`
3. Use PerplexityBrowser to get HTML
4. Use FinanceExtractor to extract answer, citations, tickers
5. Build a FinanceAnswer object with all fields filled
6. Use JsonStore to save it
7. Print this to terminal after saving:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
QUESTION : Should I buy Reliance Industries stock this week?
TICKERS  : RELIANCE
WORDS    : 203
SAVED TO : data/20240115_143022_should_i_buy_reliance.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ANSWER:
Reliance Industries is currently trading near...
[full answer text here]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## FILE 8 — README.md

Write a simple README with these exact sections:

### Setup
```bash
pip install -r requirements.txt
playwright install chromium
```

### Run
```bash
python main.py "Should I buy Reliance Industries stock this week?"
python main.py "NIFTY 50 outlook this week"
python main.py "Is Infosys a good buy right now?"
```

### Output
Every run creates one JSON file in the `data/` folder.
The filename is based on your question + timestamp.

### JSON file example
```json
{
  "query": "Should I buy Reliance Industries stock this week?",
  "answer_text": "Reliance Industries is currently...",
  "tickers_mentioned": ["RELIANCE"],
  "citations": ["https://...", "https://..."],
  "query_timestamp": "2024-01-15T14:30:22",
  "word_count": 203,
  "extraction_success": true,
  "source_url": "https://www.perplexity.ai/finance"
}
```

---

## IMPORTANT RULES FOR COPILOT

1. Build every file listed above. Do not skip any.
2. All imports must be at the top of each file.
3. Use loguru for all logging. No print statements inside classes.
4. Use async/await throughout browser.py and save.py.
5. main.py ties everything together — import from all other modules.
6. config.py is the only place with hardcoded values. Everything else reads from config.
7. If a selector fails, always try the next fallback selector before raising an error.
8. The data/ folder must be created automatically. User should never create it manually.
9. After building all files, run: `pip install -r requirements.txt && playwright install chromium`
10. Then test with: `python main.py "Should I buy Reliance Industries stock this week?"`

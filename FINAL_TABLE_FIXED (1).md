# INDIA INTRADAY TRADING — FINAL INFORMATION TABLE (CORRECTED)
# Think like an experienced Indian intraday trader
# All 15 documents read line by line | 50 cross-questions done | June 2026
# Revision: 48 errors corrected across 7 audit passes — see CHANGELOG at end of document
# Three phases: PRE-MARKET | LIVE MARKET | POST-MARKET

---

# PHASE 1 — PRE-MARKET (4:00 AM to 9:14 AM)

---

## TABLE 1A — INDEX REFERENCE LEVELS (compute before 9:15 AM every day)

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 1 | GIFT Nifty current level | Where India will open | NSE GIFT / broker |
| 2 | GIFT Nifty gap from previous Nifty close | Size tells sentiment strength | Calculate manually |
| 3 | GIFT Nifty Gap Ratio (gap ÷ 30-day SD) | Above 1.8 = fade. Below 0.8 with big US = follow | Calculate from stored data |
| 4 | GIFT Nifty hourly move 4 AM to 5:30 AM | Stable = conviction. Volatile = noise | NSE GIFT data |
| 5 | GIFT Nifty OI overnight build | FII adding or reducing futures exposure | NSE derivatives |
| 6 | Nifty Previous Day High (PDH) | First resistance if opens gap up | NSE Bhavcopy yesterday |
| 7 | Nifty Previous Day Low (PDL) | First support if opens gap down | NSE Bhavcopy yesterday |
| 8 | Nifty Previous Week High (PWH) | Stronger resistance. Fewer touches | Weekly chart |
| 9 | Nifty Previous Week Low (PWL) | Stronger support. Fewer touches | Weekly chart |
| 10 | Nifty Previous Month High (PMH) | Institutional reference. Very strong | Monthly chart |
| 11 | Nifty Previous Month Low (PML) | Institutional reference. Very strong | Monthly chart |
| 12 | Nifty Annual Pivot R1 R2 S1 S2 | Permanent for full year. Institutions use | Calculate from previous year OHLC |
| 13 | Nifty Weekly Pivot R1 R2 S1 S2 | Calculated every Monday. Weekly roadmap | Calculate from previous week OHLC |
| 14 | Nifty 52-week High | Psychological ceiling. Breakout or rejection | nseindia.com |
| 15 | Nifty 52-week Low | Psychological floor. Breakdown or bounce | nseindia.com |
| 16 | Nifty Round psychological levels | 22000, 22500, 23000 etc. Order clusters | Know from chart |
| 17 | Nifty 14-day ATR | Sets realistic stop-loss distance for today | Calculate from daily data |
| 18 | Nifty Previous Day VWAP | Above = bulls in control. Below = bears | NSE / broker |
| 19 | Nifty market structure | Uptrend, downtrend, or range for today | Daily chart |
| 20 | Nifty PE ratio | Valuation context. Above 22 = expensive | nseindia.com |
| 21 | Nifty PE vs own 10-year average | Relative expensive or cheap | Historical calculation |
| 22 | BankNifty PDH and PDL | Bank-specific first support/resistance | NSE Bhavcopy yesterday |
| 23 | BankNifty PWH and PWL | Stronger bank levels for the week | Weekly chart |
| 24 | BankNifty 14-day ATR | Bank trade stop-loss calibration | Calculate |
| 25 | BankNifty previous day VWAP | Bank institutional reference | NSE / broker |
| 26 | Sensex PDH and PDL | Cross-check with Nifty for divergence | BSE Bhavcopy |
| 27 | Sector indices overnight change | Which sector has tailwind or headwind | NSE sector indices |
| 28 | TODAY expiry check — which index? | Different protocol on expiry day | NSE / BSE derivatives calendar |
| 29 | Max pain level for today's expiry | Gravity target if today is expiry | Compute from option chain |
| 30 | Is today rollover week? (Fri–Mon before last **Tue** NSE expiry) | All options signals degraded 40% | Know from calendar |

---

## TABLE 1B — GLOBAL MACRO

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 31 | US Sector ETFs XLK XLF XLE XLI XLV closing | Sector that led US = India opening bias | Investing.com / Yahoo Finance |
| 32 | VIX ÷ VX1 term structure ratio | **Above 1.0** = backwardation/inverted term structure = cut all position sizes 50% today. Below 1.0 = normal contango (calm markets, no action needed) | Yahoo Finance |
| 33 | DXY 60-minute slope | Above +0.02%/hr = FII selling building | Investing.com |
| 34 | USD/INR overnight NDF rate | Rupee opening direction. Better than DXY | Any forex feed |
| 35 | US 10-year yield level | Above 4.5% = FII selling India equities | treasury.gov |
| 36 | US 2-10 spread (steepening or flattening) | Steepening = Bank Nifty tailwind | treasury.gov |
| 37 | US Treasury auction tail (last auction) | Large tail = yield spike upcoming | treasury.gov |
| 38 | CBOE SKEW Index | Above 145 = institutions buying tail protection | cboe.com |
| 39 | VIX9D (9-day VIX) | Near-term fear gauge more precise | cboe.com |
| 40 | CFTC Commitment of Traders (Friday) | Extreme hedge fund positioning = reversal signal | cftc.gov |
| 41 | INDA / EPI ETF pre-market quotes | Global investors buying or selling India overnight | NYSE pre-market |
| 42 | India sovereign CDS 5-year spread | Widening 15bp in session = FII selling in 1-3 days | Investing.com derivatives |
| 43 | EM bond ETF (EMB) price | EM credit stress proxy | NYSE |
| 44 | Nikkei 225 close + cause | Yen-driven vs genuine risk-on = different India read | Any financial site |
| 45 | KOSPI close + cause | Semiconductor news = Indian IT read-through | Any financial site |
| 46 | Hang Seng close + cause | China stimulus = metals/commodity read-through | Any financial site |
| 47 | Shanghai Composite close | Metals, chemicals, China-linked companies | Any financial site |
| 48 | Caixin China PMI (7:15 AM IST, 1st biz day) | China manufacturing health before session | S&P Global / Caixin website |
| 49 | USD/CNH overnight | Yuan fall = China stress = EM contagion | Forex feeds |
| 50 | Asian CDS iTraxx Asia ex-Japan | Rising spreads = FII equity selling ahead | Investing.com |
| 51 | Brent crude overnight move AND its cause | EIA vs geopolitics vs OPEC = different trade duration | Reuters / Investing.com |
| 52 | LME Copper overnight | Best free macro leading indicator | lme.com |
| 53 | MCX gold, crude, copper, aluminum prices | Real-time commodity link during Indian hours | mcxindia.com |
| 54 | Dalian Iron Ore Futures 4-week trend | Below -15% = steel margin expansion in 6-8 weeks | Investing.com |
| 55 | LME Aluminum | Hindalco upstream direct signal | lme.com |
| 56 | JKM LNG spot price | IGL, MGL, Gujarat Gas input cost | LNG price aggregators |
| 57 | Natural gas **monthly** APM revision (not daily Henry Hub) | Only this monthly revision hits IGL/MGL city gas cost (monthly since Apr 2023 Kirit Parikh reform; was quarterly before) | Ministry of Petroleum |
| 58 | Baltic Dirty Tanker Rate (VLCC, Suezmax) | Great Eastern Shipping tanker revenue signal | balticexchange.com |
| 59 | Baltic Dry Index (BDI) | Great Eastern also has 14 dry bulk ships | balticexchange.com |
| 60 | Container Freight SCFI / WCI weekly | Exporter margin pressure for textiles, chemicals | Shanghai Shipping Exchange sse.net.cn (SCFI) / Drewry (WCI) — Freightos publishes FBX, not SCFI |
| 61 | API crude (Tuesday US evening = Wednesday IST morning) | OMC/aviation signal one day before EIA | API releases / news |
| 62 | NCDEX agri futures settlement prices | FMCG and textile input cost signal | ncdex.com |

---

## TABLE 1C — INDIA REGULATORY (primary sources 30-90 min before media)

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 63 | NSE corporate filing JSON endpoint overnight | Results 10-25 min before media | nseindia.com (DevTools) |
| 64 | BSE corporate filing JSON endpoint overnight | Cross-verify both exchanges | bseindia.com (DevTools) |
| 65 | XBRL result tags (NetProfit, EBITDA, Revenue) | Parse in under 100ms without PDF | NSE/BSE XBRL format |
| 66 | Management prepared remarks in results | Before analyst questions = honest window | Company PDF filing |
| 67 | Insider window closure filings | Material event coming in 1-4 weeks | nseindia.com filings |
| 68 | Insider window opening filings | Blackout lifted. Watch promoter buys in 5 days | nseindia.com filings |
| 69 | Promoter open market buy within 5 days of window open after bad news | Strongest insider confidence signal | NSE/BSE bulk deals |
| 70 | SEBI enforcement section overnight | Ex-parte orders move stocks 10-20% | sebi.gov.in |
| 71 | SEBI ex-parte interim order | Most severe. Issued without notice | sebi.gov.in |
| 72 | SEBI preliminary investigation announcement | Early warning before ex-parte | sebi.gov.in |
| 73 | SAT orders overnight | Stay on SEBI action = stock rally | sat.gov.in |
| 74 | NCLT Section 7 petitions (financial creditor) | Bank acknowledged NPA. 1-3 days before media | nclt.gov.in / ibbi.gov.in |
| 75 | NCLT Section 9 petitions (operational creditor) | Vendor not paid. Cash is gone signal | nclt.gov.in |
| 76 | NCLAT orders overnight | Reverses NCLT order. Different website | nclat.gov.in |
| 77 | RBI LAF daily position | Surplus = cheap credit. Deficit = tight | rbi.org.in |
| 78 | CCIL call money overnight rates | Confirms or contradicts LAF | ccilindia.com |
| 79 | RBI penalty orders on banks/NBFCs | Posted before any media | rbi.org.in |
| 80 | MCA charge filings CHG-1/4/8 | ARC lender identity = bank sold stressed debt | mca.gov.in |
| 81 | FDA warning letters (updated Tuesdays only) | OAI = Warning Letter in 2-6 months | fda.gov |
| 82 | FDA ANDA approvals | First-to-file 180-day exclusivity = large revenue | fda.gov |
| 83 | CCI orders | Merger clearance/rejection 30-60 min early | cci.gov.in |
| 84 | NPPA drug price notifications | Mandatory price cut = direct pharma revenue hit | nppa.gov.in |
| 85 | FSSAI product recalls/suspensions | FMCG recalls 60-90 min before media | fssai.gov.in |
| 86 | BIS license revocations | Electronics cannot sell without BIS | bis.gov.in |
| 87 | Ministry of Defence press releases | HAL/BEL/GRSE orders before exchange | mod.gov.in |
| 88 | CBIC tariff XML notifications | Import/export duty change direct sector impact | cbic.gov.in |
| 89 | PIB/DPIIT notifications | PLI disbursements, policy approvals | pib.gov.in |
| 90 | TRAI orders | Telecom pricing and spectrum decisions | trai.gov.in |
| 91 | IRDAI circulars | Insurance company regulation changes | irdai.gov.in |
| 92 | DGFT export/import notifications | Sudden export ban = CRITICAL | dgft.gov.in |
| 93 | Related party transaction disclosures | Large fund transfers to promoter group = diversion | NSE/BSE filings |
| 94 | Forensic audit disclosures | Fund diversion more severe than accounting error | NSE/BSE filings |

---

## TABLE 1D — RATINGS AND CREDIT

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 95 | CRISIL/ICRA/CARE CP downgrades | 3-4 month early warning on longer-term cut | Rating agency websites |
| 96 | Credit outlook change Stable to Negative | 6-12 months before actual rating cut | Rating agency websites |
| 97 | Credit CreditWatch/Rating Watch status | 30-90 days before downgrade | Rating agency websites |
| 98 | Credit rating UPGRADES | Reduced funding cost = NBFC competitive edge | Rating agency websites |
| 99 | FIMMDA corporate bond yield matrix | Rising AAA-to-Gsec spread = credit risk rising | fimmda.org |
| 100 | FIMMDA commercial paper yields | NBFC short-term funding cost signal | fimmda.org |
| 101 | CCIL bond settlement data (G-Secs only) | G-sec default = sovereign stress | ccilindia.com |
| 102 | NSE Clearing/ICCL corporate bond settlement | Corporate bond default (NOT CCIL for this) | nseclearing.in / icclindia.com |

---

## TABLE 1E — MECHANICAL FORCES (forced buying/selling)

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 103 | NSE MWPL velocity = (**FutEq OI** - 5day avg) ÷ MWPL | Above 0.03/day + above 75% = ban in ~7 days. Note: (1) Post-Oct 1 2025 SEBI rules use **FutEq OI** (delta-adjusted Future Equivalent OI), not raw OI. (2) MWPL is now **lower of 15% of free float or 65×ADDV** (replaced old 20% of free float) | nseindia.com MWPL page |
| 104 | F&O ban list today | **Post Dec 8 2025 rule:** During ban, new positions ARE permitted if they reduce net FutEq OI by end of day. Rollover trades also explicitly allowed. Old rule "no new positions at all" is superseded. See #105 for the FutEq delta-reduction requirement | nseindia.com |
| 105 | F&O ban Dec 8 2025 rule — FutEq OI must reduce | Derivative trades must reduce delta exposure | Know the rule |
| 106 | ASM additions | 50% margin next day = forced selling today | NSE/BSE circulars |
| 107 | ESM (Enhanced Surveillance Measure) | Different from ASM. Financially stressed companies | NSE/BSE circulars |
| 108 | GSM additions | Graded margin requirements. Forced liquidation | NSE/BSE circulars |
| 109 | FPI headroom per company (NSDL) | Default FPI limit = sectoral cap for that company (since Apr 1 2020 reform). 24% cap only where board/shareholder has specifically resolved it. Check actual headroom per company, not a flat 24% | fpi.nsdl.co.in |
| 110 | DIPAM OFS calendar | Floor price = support. Institutions buy at floor | dipam.gov.in / pib.gov.in |
| 111 | IPO anchor lock-in Day 30 from allotment | 50% of anchor shares unlock. Selling pressure | IPO allotment date calendar |
| 112 | IPO anchor lock-in Day 90 from allotment | Other 50% unlocks. Often larger event | IPO allotment date calendar |
| 113 | MSCI IMI rebalancing calendar | Buy on announcement, sell 2 days before effective | msci.com |
| 114 | Nifty 50 semi-annual rebalancing (Mar/Sep) | Bigger passive flows than MSCI IMI | nseindia.com |
| 115 | NSE F&O segment additions today | Hedging demand = mechanical buying of underlying | NSE circulars |
| 116 | NSE F&O segment removals today | Forced unwinding follows | NSE circulars |
| 117 | Board meeting dates (2 working-day LODR advance — SEBI LODR Reg 29) | Upcoming dividend, buyback, QIP signal | NSE/BSE filings |
| 118 | Today's results calendar (which watchlist stocks) | Know which stocks carry results risk | NSE/BSE calendar |
| 119 | ESOP vesting dates | Predictable employee selling pressure | Annual report calendar |
| 120 | Open offer price under Takeover Code | Mechanical price floor for target stock | NSE/BSE filings |
| 121 | Buyback ceiling price | Company = mechanical buyer at known level | NSE/BSE filings |
| 122 | Advance tax dates (15 Jun/Sep/Dec/Mar) | Higher than prior year = internal profit confidence | Financial media monitoring |
| 123 | SAST creeping acquisition approaching 25% | Mandatory open offer imminent | NSE/BSE SAST page |
| 124 | Dividend ex-dates for Nifty heavyweights | Stop-losses auto-trigger on ex-date. Adjust them | NSE corporate actions |
| 125 | Quarter-end last 2 trading days | MF window dressing = mechanical buying of winners | Calendar awareness |
| 126 | SIP dates (1st, 5th, 7th, 10th, 15th of month) | Predictable MF buying = mild index tailwind | Calendar awareness |

---

## TABLE 1F — DERIVATIVES STRUCTURE PRE-MARKET

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 127 | Net GEX sign (positive or negative) | Single most important number. Dampening vs amplifying | Compute: Gamma × OI × ContractSize × Spot² × 0.01 |
| 128 | GEX by individual strike | Price gravitates between high-gamma bands | Compute from option chain |
| 129 | ATM PCR (strike nearest to spot only) | Above 2.5 = put-write support. Below 0.4 = resistance | Broker / NSE option chain |
| 130 | Weekly PCR vs monthly PCR separately | Different stories. Weekly = intraday, monthly = positional | Broker data |
| 131 | Max pain distance from current spot | Expiry gravity point. Above 200pts on **Tuesday** (NSE Nifty 50 expiry) = trade | Compute from option chain |
| 132 | IV rank (52-week percentile) | Above 80th = sell options. Below 20th = buy options | Stored daily IV database |
| 133 | IV ÷ HV20 ratio | Above 1.3 = prefer equity/futures. Below 0.8 = buy options | Compute from stored data |
| 134 | Put-call skew (OTM put IV - ATM call IV) | Steepening even when ATM flat = tail demand rising | Broker / option chain |
| 135 | Futures basis annualized | 3+ sessions inverted = institutional short accumulation | Broker data |
| 136 | FII combined position (cash + Nifty fut + BankNifty fut) | True directional bet. Never use cash data alone | NSE FII derivatives page |
| 137 | FII **Category I and II** breakdown (no Category III since SEBI FPI Regs 2019) | Cat I = sovereign/regulated = structural. Cat II = all others incl. hedge funds = reverses fast | NSE / NSDL |
| 138 | USD/INR futures OI on NSE | FIIs buy USD/INR as they sell equities = proxy | nseindia.com derivatives |

---

## TABLE 1G — PRE-OPEN MICROSTRUCTURE (8:45 AM to 9:07 AM)

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 139 | Block deals 8:45-9:00 AM | Above 500Cr at discount = motivated seller, bearish 2-5 days | NSE/BSE live announcements |
| 140 | Block deal volume vs 5-day ADV (mid-cap) | 15% of 5-day volume = significant regardless of rupee | Calculate |
| 141 | Pre-open order book imbalance 9:00-9:07 AM | 4:1 buy-to-sell = clean trending open | Broker API |
| 142 | Pre-open equilibrium vs GIFT Nifty implied | Divergence = first arbitrage signal of day | Compare levels |
| 143 | IPO GMP on listing day (ipowatch.in) | Above 30% = momentum listing (treat as context only) | ipowatch.in / chittorgarh.com |

---

## TABLE 1H — ECONOMIC AND SECTOR DATA

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 144 | India CPI (scheduled release) | Inflation regime. Rate expectations | mospi.gov.in |
| 145 | India WPI Monthly | Corporate input cost pressure | eaindustry.nic.in (Office of Economic Adviser; DIPP renamed DPIIT in 2018 — no longer publishes WPI) |
| 146 | India IIP Monthly | Industrial production | mospi.gov.in |
| 147 | India GDP Quarterly | Growth regime | mospi.gov.in |
| 148 | India Trade Deficit Monthly | Rupee pressure signal | commerce.gov.in |
| 149 | GST Collection Monthly (1st of month) | Fiscal health | finmin.nic.in |
| 150 | India Forex Reserves Weekly (Friday 5:30PM) | Rupee stability | rbi.org.in |
| 151 | RBI Bank Credit Fortnightly | Bank Nifty fundamental | rbi.org.in |
| 152 | PPAC Petroleum Consumption (Wednesday) | HSD decline = industrial slowdown 6-8 wks ahead | ppac.gov.in |
| 153 | PPAC ATF prices (1st and 16th of month) | IndiGo fuel cost. 10% change = 4-5% OpEx impact | ppac.gov.in |
| 154 | Steel Ministry Weekly Production | Tata Steel, JSW, SAIL revenue signal | steel.gov.in |
| 155 | Coal India Daily Production (7 AM) | Power sector, cement input signal | coalindia.in |
| 156 | CEA Daily Power Generation | Coal shortage, power deficit signal | cea.nic.in |
| 157 | Railway Freight Loading Weekly | Commodity demand signal | indianrailways.gov.in |
| 158 | IMD Weekly Monsoon Progress | Agri sector 8-10 week lead | imd.gov.in |
| 159 | NMDC Daily Iron Ore Production | Steel input cost signal | nmdc.co.in |
| 160 | APMC Mandi arrivals and prices | FMCG raw material cost signal | agmarknet.nic.in |
| 161 | Sugar Directorate daily crushing (season) | Balrampur, Dhampur revenue signal | Sugar directorate |
| 162 | DGCA Monthly Passenger Traffic | IndiGo market share signal | dgca.gov.in |
| 163 | Cement dispatch monthly (CMA) | Ultratech, Shree, ACC demand | cmaindia.org |
| 164 | Pharmexcil monthly pharma export | Pharma revenue before results | pharmexcil.com |
| 165 | NASSCOM quarterly IT exports | IT sector signal before company results | nasscom.in |
| 166 | VAHAN auto retail sales | Actual retail demand. More accurate than SIAM | vahanreports.parivahan.gov.in |
| 167 | Tractor sales monthly (TMA) | Rural demand signal | TMA releases |
| 168 | MSME Samadhaan payment delays | Cash flow stress 30-90 days ahead | samadhaan.msme.gov.in |
| 169 | EPFO Monthly Subscribers | Formal employment signal | epfindia.gov.in |
| 170 | TiO2 prices weekly | Paint company (Asian Paints, Berger) margin | Pricing services |
| 171 | PVC resin prices weekly | Pipe company (Astral, Supreme) margin | Pricing services |
| 172 | Pet coke prices weekly | Cement fuel cost (Ultratech, Ambuja) | Pricing services |
| 173 | Caustic soda prices weekly | Aluminum **refining** cost (Bayer process — NaOH has no role in smelting/Hall-Héroult) | Pricing services |
| 174 | Cobalt and lithium spot prices | EV battery input for Tata Motors EV | Commodity sites |
| 175 | Today's scheduled macro releases | Know what drops during live session | Economic calendar |
| 176 | US FOMC / ECB / BOJ today? | Global rate decision = afternoon volatility | Fed/ECB/BOJ calendars |

---

# PHASE 2 — LIVE MARKET (9:15 AM to 3:30 PM)

---

## TABLE 2A — INDEX LIVE MONITORING

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 1 | Nifty vs PDH/PDL live | Above PDH = breakout. Below PDL = breakdown | Broker / NSE live |
| 2 | Nifty vs PWH/PWL live | Stronger levels. Bigger moves if breached | Broker |
| 3 | Nifty vs VWAP live | Above = institutional buying. Below = selling | Broker |
| 4 | Nifty vs 15-minute ORB (9:15-9:30) | Primary support/resistance for today | Broker |
| 5 | Nifty vs 30-minute ORB (9:15-9:45) | Secondary reference level | Broker |
| 6 | Nifty current market structure live | Higher highs/lows = uptrend. Take longs at pullbacks | Broker chart |
| 7 | BankNifty vs Nifty ratio live | Below 5-day avg = banks lagging. Broader correction risk | Broker |
| 8 | Sensex vs Nifty divergence live | Above 0.3% divergence = manipulation by few stocks | Broker |
| 9 | Nifty intraday point of control (highest volume price) | Afternoon mean reversion magnet | Broker / volume profile |
| 10 | Nifty futures premium/discount beyond 15 points | Forced institutional arbitrage happening | Broker |
| 11 | Nifty constituent contribution to index move | Concentrated in 2-3 stocks = not genuine trend | Broker |
| 12 | Top 10 Nifty heavyweights above/below morning open | 7 of 10 below open = propped index. Fragile rally | Broker |
| 13 | Call wall and put wall proximity live | Resistance/support intensifying as price approaches | Broker / option chain |

---

## TABLE 2B — PROFIT WINDOWS AND TIMING (know before session)

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 14 | 9:20 AM to 10:30 AM | First institutional flow window. Highest probability | Know and follow |
| 15 | 11:30 AM to 1:30 PM | Dead zone. Lowest volume. Reduce size to 60% or skip | Know and follow |
| 16 | 1:45 PM to 2:45 PM | Second institutional flow window | Know and follow |
| 17 | Index direction first 15 minutes | Trades aligned with Nifty direction = 1.6x win rate | Observe first 15 min |
| 18 | 2-4 trades per day optimal | Beyond 5 trades = success rate drops 40% | Know and follow |

---

## TABLE 2C — OPTIONS AND DERIVATIVES LIVE

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 19 | ATM PCR crossing above 3.0 | Put-write support establishing at that level | Broker WebSocket |
| 20 | ATM PCR falling below 0.35 | Call-write resistance establishing | Broker WebSocket |
| 21 | GEX sign flip during session | Entire execution strategy changes immediately | Compute live |
| 22 | GEX by strike live | Price oscillates between high-gamma bands | Compute live |
| 23 | OI velocity at strike (3x its 30-min avg) | New institutional level being built right now | Broker data |
| 24 | India VIX — 5% spike from open | Reduce positions 25% | NSE / broker |
| 25 | India VIX — 8% spike from open | Reduce positions 50% | NSE / broker |
| 26 | India VIX — 12% spike from open | Stop all option selling | NSE / broker |
| 27 | India VIX — 15% spike from open | Reduce all positions 75% | NSE / broker |
| 28 | Max pain gravity (**Tuesday** = NSE Nifty expiry, 2PM, 200+ pts away) | Align orders toward max pain until 3:00 PM — no new positions after 3:00 PM | Compute |
| 29 | Fresh put OI added vs call OI per 15 min | New active positioning. Different from cumulative PCR | Broker data |
| 30 | Option volume at strike vs 20-day average | 5x above average = informed money at that strike | Broker data |
| 31 | Total option premium outstanding value | Sudden spike = event risk money entering | Broker data |
| 32 | USD/INR futures OI change during session | FIIs selling equities = buying USD/INR simultaneously | nseindia.com |
| 33 | FIMMDA CP yields live | NBFC funding cost spike = same-session signal | fimmda.org |
| 34 | Option chain data freshness | Stale above 5 minutes = GEX unreliable | Broker API check |

---

## TABLE 2D — EXPIRY DAY SPECIFIC RULES

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 35 | Which index expires today — WEEKLY: **Tue=NSE Nifty 50 only, Thu=BSE Sensex only**. MONTHLY (last week): Mon=Bankex, **Tue=Nifty 50+BankNifty, Thu=Sensex+FinNifty**, Wed=MidcapNifty | Different protocol each day. Day assignments as of Sep 1 2025 (NSE: Thu→Mon Apr 2025→Tue Sep 2025; BSE: Tue→Thu Sep 2025) | NSE/BSE calendar |
| 36 | Max pain distance at 2PM on expiry | Most reliable gravity signal. Trade toward max pain | Compute at 2PM |
| 37 | Theta decay in last 90 minutes | Even correct direction = premium goes to zero | Know the rule |
| 38 | Never buy options after 2PM on expiry | Theta destroys faster than price moves | Know the rule |
| 39 | Gamma explosion near ATM on expiry | Price can move 2-3% in minutes near strikes | Monitor closely |
| 40 | Physical settlement check for ITM stock options | Must close before expiry or receive/deliver shares | Broker check |
| 41 | Monthly expiry vs weekly (NSE = last **Tuesday**, BSE = last **Thursday**) | Monthly max pain most reliable. Institutional writers largest | Calendar check |
| 42 | IV crush during results conference call | Most IV gone in first 15 minutes of call | Know the rule |

---

## TABLE 2E — BREAKING NEWS AND CORPORATE EVENTS

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 43 | NSE/BSE filing stream every 45 seconds | Beat or miss parsed before any media | JSON endpoint / broker |
| 44 | SEBI enforcement every 8 minutes | Ex-parte orders move stocks 10-20% | sebi.gov.in |
| 45 | SAT orders every 15-20 minutes | Stay reverses SEBI action. NEVER check only at 4PM | sat.gov.in |
| 46 | FDA OAI classification (fda.gov) | 30-90 minute window before exchange announcement | fda.gov |
| 47 | Conference call live transcription | Prepared remarks before analysts = honest window | Whisper on audio stream |
| 48 | Exchange query letters during session | Stop adding longs on queried stock immediately | NSE/BSE |
| 49 | Unknown catalyst detector (2%+ in 20 min, no news) | Institutional informed activity. Reduce exposure | Monitor live |
| 50 | RBI OMO bond purchase announcement | Immediate Bank Nifty bullish signal | rbi.org.in |

---

## TABLE 2F — MACRO RELEASES DURING SESSION

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 51 | India Manufacturing PMI 9:30 AM IST (1st biz day) | Above 55 = bullish. Below 50 = regime changes | S&P Global website |
| 52 | HSBC India **Services** PMI 10:30 AM IST (**3rd biz day**) | After session open. Confirms or contradicts. Note: 1st biz day = Manufacturing PMI only (item 51); Services PMI is a separate survey released 3rd biz day | S&P Global release (IHS Markit merged with S&P Global Feb 2022; "Markit" brand retired) |
| 53 | RBI MPC decision ~10 AM IST (day 3) | Stance change MORE important than rate itself | rbi.org.in |
| 54 | RBI governor press conference (~10:30 AM) | Tone determines hawkish/dovish interpretation | rbi.org.in live |
| 55 | G-sec auction devolvement (Fri 11:30AM-2PM) | Primary dealers absorb = yield spike = Bank Nifty down | rbi.org.in |
| 56 | T-bill auction (every Wednesday) | Short-term liquidity stress. MIBOR signal | rbi.org.in |

---

## TABLE 2G — GLOBAL LIVE SIGNALS

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 57 | Shanghai Composite — morning session ends **9:00 AM IST** (11:30 AM CST); afternoon resumes **10:30 AM IST** (1:00 PM CST). Lunch break 9:00–10:30 AM IST | Metals, chemicals, China-linked same session | Any financial site |
| 58 | Hang Seng — afternoon session resumes **10:30 AM IST** (1:00 PM HKT). HKEX lunch break 9:30–10:30 AM IST (12:00–1:00 PM HKT); 9:45 AM IST = 12:15 PM HKT = inside lunch break | IT, metals, FII sentiment same session | Any financial site |
| 59 | MCX gold, crude, copper, aluminum live | Real-time commodity to equity link | mcxindia.com |
| 60 | NCDEX cotton, soybean live | Textile, FMCG sector signal | ncdex.com |
| 61 | IEX real-time power prices | Power sector stocks same session | iexindia.com |
| 62 | USD/CNH live (0.3% threshold) | EM contagion triggered within same session | Forex feeds |
| 63 | US bond futures from 2:00 PM IST | Bank Nifty last 90 minutes signal | Futures data feeds |
| 64 | Europe open DAX/FTSE — **12:30 PM IST** (summer: CEST/BST, late Mar–late Oct) or **1:30 PM IST** (winter: CET/GMT, late Oct–late Mar) | Can reverse Indian afternoon trajectory | Any financial site |
| 65 | US pre-market futures from 2:00 PM IST | GIFT Nifty for next morning forming now | Futures data feeds |
| 66 | PBOC daily USD/CNY fixing (6:45 AM IST) | Moves Asian markets. Check before session | PBOC / news |

---

## TABLE 2H — MARKET BREADTH AND HEALTH

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 67 | Advance-decline ratio Nifty 500 every 15 min | Internal health invisible from index level | Broker / NSE |
| 68 | Nifty 50 stocks above VWAP count | Below 20 = institutional selling broad. Index misleading | Broker |
| 69 | Nifty 50 stocks above 5-day MA count | Below 20 while index flat = internal deterioration | Broker |
| 70 | New 52-week highs vs new 52-week lows | Distribution happening invisibly | NSE / broker |
| 71 | Full market circuit hit count | 50+ lower circuits in 30 min = panic. Nifty may lie | NSE |
| 72 | Smallcap 250 vs Nifty 50 ratio | Retail risk appetite signal | Broker |
| 73 | Defensive vs cyclical ratio live | FMCG+Pharma ÷ Metal+Auto rising = risk-off building | Broker |
| 74 | Sector rotation heatmap (8 sectors vs Nifty) | Real-time capital direction every 15 minutes | NSE sector indices / broker |

---

## TABLE 2I — MICROSTRUCTURE LIVE

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 75 | VWAP live per watchlist stock | Bullish event but below VWAP = wait for reclaim first | Broker |
| 76 | NSE SBL inventory sudden increase | Institutions borrowing to short = 1-2 day lead | nseindia.com SBL page |
| 77 | Afternoon bulk deals during session | Any entity above 0.5% of listed shares = flag immediately | NSE/BSE |
| 78 | NEFT/RTGS aggregate daily value | Sudden drop = corporate payment stalled = credit stress | RBI website |

---

# PHASE 3 — POST-MARKET (3:30 PM onwards, for tomorrow)

---

## TABLE 3A — INDEX END-OF-DAY DATA (compute for tomorrow)

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 1 | Nifty OHLCV today | Tomorrow's PDH and PDL. Primary reference | NSE Bhavcopy |
| 2 | BankNifty OHLCV today | Tomorrow's Bank PDH and PDL | NSE Bhavcopy |
| 3 | Nifty closing VWAP | Tomorrow's institutional reference level | NSE / broker |
| 4 | BankNifty closing VWAP | Tomorrow's bank institutional reference | NSE / broker |
| 5 | All 8 sector indices closing | Tomorrow's relative strength map | NSE sector data |
| 6 | Nifty weekly OHLC (if today is Friday) | Next week's PWH, PWL, weekly pivots | NSE Bhavcopy |
| 7 | India VIX closing level | Update 52-week percentile database | NSE |
| 8 | All option OI by strike at close | Tomorrow's GEX computation baseline | Broker / NSE |
| 9 | Option OI change today by strike | Which strikes built, which reduced = tomorrow's levels | Broker data |
| 10 | Nifty PE, PB, dividend yield at close | Tomorrow's valuation context | nseindia.com |
| 11 | Nifty futures closing basis annualized | Institutional positioning context | Broker data |

---

## TABLE 3B — CRITICAL FLOW DATA

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 12 | NSE delivery % per stock after 8PM | High delivery on down day = institutional accumulation | NSE Bhavcopy |
| 13 | Delivery % for all 50 Nifty constituents | Broad accumulation vs narrow signal | NSE Bhavcopy |
| 14 | Provisional FII/DII cash data (3:45-4:00 PM) | Same-day cash flow direction | NSE/BSE |
| 15 | Revised provisional FII data (6:30 PM NSE) | Most important number for tomorrow's regime | NSE |
| 16 | Final FII derivatives (cash + Nifty fut + BankNifty fut) | True combined position. Cash alone misleads | NSE FII derivatives page |
| 17 | FII **Category I and II** breakdown (SEBI FPI Regs 2019 — no Category III) | Cat I = structural/sovereign. Cat II = hedge funds and others — reverses fast | NSE / NSDL |
| 18 | AMFI daily MF flow (after 9 PM) | Redemption pressure for tomorrow | amfiindia.com |
| 19 | India ADR prices on NYSE (INFY, HDB, IBN, RDY, WIT) | Premium/discount to NSE = FII overnight sentiment. Note: TTM (Tata Motors) delisted its NYSE ADR in Jan 2023 — removed | NYSE after-hours |

---

## TABLE 3C — EXCHANGE UPDATES EVERY EVENING

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 20 | NSE Bhavcopy full download | OHLCV, delivery% for every instrument | nseindia.com |
| 21 | NSE MWPL (FutEq OI basis) — checked **4 random times intraday** since Oct 2025 | Stocks can enter ban **during live session hours**, not only overnight. Update ban calendar but also monitor intraday. "3-5 day ban calendar" logic from post-market alone is now insufficient | nseindia.com |
| 22 | ASM/ESM/GSM list updates | New additions = tomorrow's forced selling. Removals = buying | NSE/BSE circulars |
| 23 | F&O ban list official (after 7 PM) | Tomorrow's derivative constraints | nseindia.com |
| 24 | NSE T2T segment migrations | No intraday trading tomorrow for migrated stocks | nseindia.com |
| 25 | After-hours corporate filings (4PM-8PM) | Tomorrow's gap setup. Many companies report here | nseindia.com/bseindia.com |
| 26 | SAST disclosures | Promoter buys, FPI threshold crossings | NSE/BSE SAST page |
| 27 | Bulk deal full session summary | Complete buyer/seller identity and price | NSE/BSE |
| 28 | NSE short selling daily data | Building short interest per stock | nseindia.com |
| 29 | NSCCL SPAN margin updates | Higher margins tomorrow = smaller positions | nseclearing.in |
| 30 | Post-market option OI change by strike | Tomorrow's GEX baseline | Broker data |
| 31 | Insider/promoter transaction filings (PIT reg) | Insider confidence signal | NSE/BSE |
| 32 | AGM/EGM voting outcomes | Promoter failing resolution = governance signal | NSE/BSE filings |
| 33 | NSE exchange circulars | Margin changes, lot size, circuit filter tomorrow | nseindia.com circulars |

---

## TABLE 3D — REGULATORY POST-MARKET

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 34 | SEBI orders after 5 PM | Tomorrow's short setup | sebi.gov.in |
| 35 | RBI circulars after 4 PM | NBFC/bank rule changes | rbi.org.in |
| 36 | RBI repo/VRR auction results | Banking system stress signal | rbi.org.in |
| 37 | NCLT/NCLAT cause lists for tomorrow | Tomorrow's hearing calendar | nclt.gov.in / nclat.gov.in |
| 38 | SAT orders missed during session | Legal reversals of SEBI actions | sat.gov.in |
| 39 | FSSAI evening notifications | FMCG recalls for tomorrow | fssai.gov.in |
| 40 | RBI LAF and CCIL call money (~8 PM) | Tomorrow's liquidity regime | rbi.org.in / ccilindia.com |
| 41 | NSE Clearing/ICCL corporate bond settlement | Corporate bond default signal (NOT CCIL) | nseclearing.in / icclindia.com |

---

## TABLE 3E — GLOBAL OVERNIGHT SIGNALS

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 42 | US market first 30 minutes — opens **7:00 PM IST** (EDT, Apr–Oct) or **8:00 PM IST** (EST, Nov–Mar) | Sets GIFT Nifty by 10 PM IST | Any financial site |
| 43 | US sector ETF closing performance | Tomorrow's sector bias | Any financial site |
| 44 | Accenture earnings | Affects TCS, Infosys, HCL guidance | Earnings reports |
| 45 | BASF earnings | Affects Indian specialty chemicals | Earnings reports |
| 46 | Lam Research/ASML earnings | Affects electronics, semiconductor companies | Earnings reports |
| 47 | Samsung earnings (KOSPI impact) | Affects KOSPI which affects Indian IT | Earnings reports |
| 48 | Amazon/Walmart earnings | Affects Indian logistics and e-commerce | Earnings reports |
| 49 | Fed speaker comments after Indian close | Hawkish/dovish = overnight regime setter | Fed website / news |
| 50 | BOJ policy decisions | Yen moves = carry trade = INR impact | BOJ website / news |
| 51 | OPEC production decisions | Crude direction for weeks. OMC stocks | OPEC / news |
| 52 | US Treasury auction results and tail | Bond demand weakness = yield spike | treasury.gov |
| 53 | Global sovereign yields overnight (US/Germany/UK/Japan) | Risk appetite for tomorrow | Any financial site |
| 54 | Commodity overnight moves WITH cause | Cause determines which India stocks to trade | Commodity sites |
| 55 | GIFT Nifty hourly data 9 PM to 5 AM | FII overnight futures positioning | NSE GIFT / broker |
| 56 | India NDF rate divergence overnight | Rupee gap open predictor | Forex feeds |
| 57 | API crude (Tuesday US evening) | OMC/aviation signal before Wednesday EIA | API / news |

---

## TABLE 3F — ECONOMIC DATA RELEASED POST-MARKET

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 58 | RBI forex reserves (Friday 5:30 PM) | Rupee stability. 3 consecutive declines = stress | rbi.org.in |
| 59 | RBI weekly statistical supplement (Friday eve) | M3, credit, deposits, forex all in one | rbi.org.in |
| 60 | GST collection (1st of month) | Fiscal health signal | finmin.nic.in |
| 61 | Flash export/import data (~20th of month) | Trade deficit and rupee pressure | commerce.gov.in |
| 62 | AMFI monthly MF flow by category | Sector rotation and dry powder | amfiindia.com |
| 63 | Advance tax data (15 Jun/Sep/Dec/Mar) | Higher than prior year = internal profit confidence | Financial media |

---

## TABLE 3G — DAILY ARCHIVE (store every day)

| # | Information | Why | Source |
|---|-------------|-----|--------|
| 64 | IV daily close per watchlist stock | Builds 52-week IV rank. Useless without history | Broker / NSE |
| 65 | ATM PCR daily close | Historical context for today's reading | Broker data |
| 66 | India VIX daily close | 52-week percentile for graduated thresholds | NSE |
| 67 | Nifty OHLCV daily | PDH/PDL for next session. Rolling historical chart | NSE Bhavcopy |
| 68 | BankNifty OHLCV daily | Same | NSE Bhavcopy |
| 69 | MWPL per stock daily | Velocity requires time series. Not just today | nseindia.com |
| 70 | GEX sign daily vs next day return | Validates regime theory in Indian market | Store and compute |
| 71 | Delivery % daily per stock | Accumulation vs distribution trend | NSE Bhavcopy |
| 72 | Sector index daily closes (IT/Bank/Pharma/Metal/Auto/FMCG) | Relative strength context | NSE |
| 73 | India 10-year G-sec yield daily | Rate trend context | NSE/RBI |
| 74 | Call money rate daily (CCIL) | Liquidity trend | ccilindia.com |
| 75 | VWAP per watchlist stock daily | Tomorrow's first execution filter | Broker |
| 76 | Signal accuracy log (event + regime + direction + outcome) | Which signals actually work = system improvement | Your own database |
| 77 | Weekly failure audit (Friday) | Every Nifty 100 stock 2%+ without your flag = fix | Your own review |

---

# EXPIRY CALENDAR REFERENCE

---

## TABLE E1 — EXPIRY SCHEDULE BY DAY (updated per SEBI standardisation effective Sep 1 2025)

> **History of changes:** (1) SEBI circular Sep 30 2024 (eff. Nov 20 2024): NSE discontinued weekly BankNifty, FinNifty, MidcapNifty; BSE discontinued weekly Bankex. (2) NSE moved Nifty 50 expiry Thu→Mon in Apr 2025, then Mon→**Tue** in Sep 2025. (3) BSE moved Sensex expiry Tue→**Thu** in Sep 2025. As of Sep 1 2025: NSE Nifty 50 = Tuesday; BSE Sensex = Thursday.

| Day | Weekly Expiry (every non-last-expiry week) | Monthly Expiry (last expiry week only) |
|-----|--------------------------------------------|----------------------------------------|
| Monday | — | BSE Bankex |
| **Tuesday** | **NSE Nifty 50 only** | **NSE Nifty 50 + NSE BankNifty** |
| Wednesday | — | NSE Nifty Midcap Select |
| **Thursday** | **BSE Sensex only** | **BSE Sensex + NSE FinNifty** |
| Friday | No major index expiry | — |

---

## TABLE E2 — EXPIRY DAY PROTOCOL BY TIME

| Time | Action | Why |
|------|---------|-----|
| 9:15 AM | Compute max pain fresh | Fresh writing from 9:15 AM shifts the strike (NSE F&O opens 9:15 AM — no option writing possible at 9:00 AM) |
| 9:15-11:30 AM | Normal session. PCR still useful | Options have time value |
| 11:30 AM-1:30 PM | Dead zone. Reduce size | Low volume, wide spreads |
| 1:45-2:00 PM | Max pain computation update | Most reliable reading of the day |
| 2:00 PM | FutEq OI delta calculated for ban rule | Dec 8 2025 rule compliance |
| 2:00-3:00 PM | Align toward max pain if 200+ points away | Gravity is strongest now; stops at 3:00 PM (no new positions after that) |
| 2:00 PM onward | Do NOT buy options | Theta destroys faster than price moves |
| 3:00 PM | No new positions at all | Risk of gamma explosion near settlement |
| 3:00-3:30 PM | Settlement window. Violent near ATM | NSE closing = VWAP of this 30 min |

---

## TABLE E3 — ROLLOVER WEEK BEHAVIOR (Friday–Monday before monthly expiry Tuesday for NSE)

| Day | Behavior | Action |
|-----|----------|--------|
| Friday (week before) | OI rollover starts. PCR starts degrading | Reduce confidence on options signals 40% |
| Monday | Heavy rollover continues | Max pain shifts daily. Do not anchor to it |
| **Tuesday** | **Main NSE expiry** (Nifty 50 + BankNifty). Highest OI, highest institutional activity | Full expiry protocol applies |
| Wednesday | New series OI thin | All NSE options signals unreliable for 3-5 days |
| **Thursday** | **BSE Sensex expiry** (weekly and monthly last Thu) | Apply expiry protocol for Sensex positions |

---

## TABLE E4 — US EXPIRY IMPACT ON INDIA

| US Event | When | India Impact |
|----------|------|-------------|
| US Monthly Options Expiry | Third Friday every month | Indian afternoon session (1:30-3:30 PM) sees higher volatility |
| US Quadruple Witching | Third Friday of March/June/Sep/Dec | Largest global volatility. Reduce India sizes |

---

## TABLE E5 — ANNUAL HIGH-IMPACT DATES

| Month | Events |
|-------|--------|
| Jan/Feb | Q3 results peak. Economic Survey Jan 31. Union Budget Feb 1 |
| February | RBI MPC |
| March | Nifty 50 semi-annual rebalancing announcement + **effective last trading day of March** (cut-off Jan 31; announcement ~4 weeks prior). Q4 advance tax Mar 15. Month-end MF window dressing |
| April | Q4 results begin. STT rates from Apr 1 (Budget 2026 rates in effect) |
| May | Q4 results peak. MSCI **Semi-Annual** Index Review (comprehensive — constituent additions/deletions; quarterly reviews are Feb/Aug, not listed here) |
| June | Q1 advance tax Jun 15. US Quadruple Witching. MSCI effective date |
| July | Q1 results begin. IT companies first |
| Aug | Q1 results peak. RBI MPC |
| Sep | US Quadruple Witching. Q2 advance tax Sep 15. Nifty rebalancing announcement + **effective end of September** |
| Oct | Q2 results begin. RBI MPC. Muhurat trading (Diwali, special rules) |
| Nov | Q2 results peak. MSCI **Semi-Annual** Index Review (comprehensive — constituent additions/deletions; Feb/Aug = quarterly reviews) |
| Dec | Q3 advance tax Dec 15. US Quadruple Witching. MSCI effective. Year-end global rebalancing |

---

# KEY CORRECTIONS (verified from all 15 documents)

| Wrong Belief | Correct Fact |
|-------------|-------------|
| CCIL settles corporate bonds | CCIL only settles G-Secs, forex, money market. Corporate bonds = NSE Clearing/ICCL |
| BDI is irrelevant for Great Eastern | Great Eastern has 14 dry bulk ships. BDI AND dirty tanker rates both matter |
| Caixin PMI at 8:45 AM IST | 7:15 AM IST (9:45 AM Beijing Time) |
| Henry Hub moves IGL/MGL | Only the **monthly** APM revision matters for city gas distributors (monthly since Apr 2023 Kirit Parikh reform — was quarterly before that). Daily Henry Hub is irrelevant |
| Anchor lock-in from listing date | From allotment date. Under T+3 framework: demat credit on T+2, listing on T+3 — allotment is **1 working day before listing**, not 3 |
| Anchor lock-in is one event | Two events: 50% at 30 days, 50% at 90 days from allotment |
| DIPAM OFS floor = short target | Floor = support. Institutions hold back then BUY at floor |
| Aggregate PCR is the signal | ATM strike PCR (nearest to spot) is the real signal |
| FDA updates daily | Warning letters only on TUESDAYS. Database lags weeks to months |
| MTF margin = VaR + 5×ELM | Correct SEBI formula is **VaR + 3×ELM** for Group 1 securities (minimum initial margin). 5× is the leverage cap, not the margin input |
| PCR below X = bullish | Store concepts not fixed numbers. Market regimes change |
| Check SAT only at 4 PM | SAT must be checked every 15-20 minutes during session. Intraday stays happen |
| SME board stocks generate signals | Exclude all NSE Emerge and BSE SME stocks from every signal source |
| Buy the dip when GEX positive | NEVER on SEBI orders, NCLT petitions, ARC lender, forensic audits |
| NSE close = last traded price | NSE close = VWAP of last 30 minutes (3:00-3:30 PM) |

---

*All sources public and free | Verified June 2026 | Based on 15-document complete audit*

---

# CHANGELOG — 48 ERRORS CORRECTED (7 audit passes)

| # | Pass | Location | Error | Fix |
|---|------|----------|-------|-----|
| 1 | 1 | Table 1B #32 | VIX÷VX1 danger signal said "below 1.0" | Corrected to "above 1.0" (backwardation = danger; below 1.0 = normal contango) |
| 2 | 1 | Table 1E #103 | MWPL ban timeline said 4 days | Corrected to ~7 days (75% + 7×0.03/day = 96% crosses 95% threshold) |
| 3 | 1 | Table 1E #117 | LODR advance notice said 5 days | Corrected to 2 working days (SEBI LODR Reg 29) |
| 4 | 1 | Table 1H #145 | WPI source said dipp.gov.in | Corrected to eaindustry.nic.in (DIPP renamed DPIIT 2018; WPI = Office of Economic Adviser) |
| 5 | 1 | Table E1 / Table 2D #35 | Weekly expiry listed BankNifty/FinNifty/MidcapNifty/Bankex as still active | Updated per SEBI circular 30-Sep-2024 (eff. 20-Nov-2024): weekly discontinued for those indices |
| 6 | 1 | Table E2 | "Fresh writing from 9:00 AM" | Corrected to 9:15 AM (NSE F&O opens 9:15 AM) |
| 7 | 1 | Table 2C #28 | "Align toward max pain until 3:15 PM" | Corrected to "until 3:00 PM" (consistent with E2 no-new-positions rule) |
| 8 | 1 | Table E2 | "2:00-3:30 PM align toward max pain" contradicted 3:00 PM cutoff row | Corrected window to "2:00-3:00 PM" |
| 9 | 1 | Table E5 (Feb) | US Quadruple Witching listed under February | Removed — occurs only Mar/Jun/Sep/Dec |
| 10 | 1 | Table E5 (Mar/Jun/Sep) | Nifty rebalancing "effective" in June; Mar/Sep lacked effective dates | Corrected: effective last trading day of March; Sep effective end of September; removed June |
| 11 | 1 | KEY CORRECTIONS | "T+3 = allotment 3 working days before listing" | Corrected: demat credit T+2, listing T+3 → allotment is 1 working day before listing |
| 12 | 1 | KEY CORRECTIONS | "Correct formula is VaR + ELM" for MTF | Corrected to VaR + 3×ELM (Group 1 securities, SEBI MTF regulations) |
| 13 | 1 | Table 3E #42 | US market open said 7:30 PM IST | Corrected: 7:00 PM IST (EDT Apr-Oct) / 8:00 PM IST (EST Nov-Mar) |
| 14 | 2 | Table 1H #173 | Caustic soda = "aluminum smelting cost" | Corrected to "aluminum refining cost" (Bayer process; no role in Hall-Héroult smelting) |
| 15 | 2 | Table 2F #52 | HSBC India Services PMI said "1st biz day" | Corrected to 3rd business day (1st biz day = Manufacturing PMI, a separate survey) |
| 16 | 2 | Table 2G #58 | Hang Seng "live" at 9:45 AM IST | Corrected: inside HKEX lunch break; afternoon resumes 10:30 AM IST |
| 17 | 2 | Table 2G #64 | Europe open DAX/FTSE fixed at 1:30 PM IST | Corrected: 12:30 PM IST (CEST/BST, late Mar–late Oct) / 1:30 PM IST (CET/GMT, late Oct–late Mar) |
| 18 | 3 | Table 2G #57 | Shanghai Composite "live" at 9:30 AM IST | Corrected: inside SSE lunch break; morning ends 9:00 AM IST, afternoon resumes 10:30 AM IST |
| 19 | 3 | Table 1B #60 | SCFI source listed as Freightos | Corrected: Freightos = FBX. SCFI = Shanghai Shipping Exchange (sse.net.cn); Drewry = WCI |
| 20 | 4 | Table 1C #78 | CCIL source = ccil.org | Corrected to ccilindia.com |
| 21 | 4 | Table 1D #101 | CCIL source = ccil.org | Corrected to ccilindia.com |
| 22 | 4 | Table 3D #40 | CCIL source = ccil.org | Corrected to ccilindia.com |
| 23 | 4 | Table 3G #74 | CCIL source = ccil.org | Corrected to ccilindia.com |
| 24 | 4 | Table 2F #52 | Source = "Markit/HSBC release" | Corrected to "S&P Global release" (IHS Markit merged into S&P Global Feb 2022) |
| 25 | 5 | Table 1C #73 | SAT source = sat-india.com | Corrected to sat.gov.in |
| 26 | 5 | Table 2E #45 | SAT source = sat-india.com | Corrected to sat.gov.in |
| 27 | 5 | Table 3D #38 | SAT source = sat-india.com | Corrected to sat.gov.in |
| 28 | 5 | Table 1D #102 | NSE Clearing source = nsccl.com | Corrected to nseclearing.in |
| 29 | 5 | Table 3C #29 | NSCCL source = nsccl.com | Corrected to nseclearing.in |
| 30 | 5 | Table 3D #41 | NSE Clearing source = nsccl.com | Corrected to nseclearing.in |
| 31 | 5 | Table 1E #109 | FPI limit described as flat 24% | Corrected: default limit = sectoral cap per company since Apr 1 2020 reform; 24% only where board/shareholder resolved it |
| 32 | 5 | Table 1B #57 | APM revision said "quarterly" | Corrected to monthly (Kirit Parikh Committee reform, Apr 2023) |
| 33 | 5 | KEY CORRECTIONS | APM revision said "quarterly" | Corrected to monthly |
| 34 | 5 | Table E1 | NSE Nifty 50 on Thursday; BSE Sensex on Tuesday | Corrected: NSE → Tuesday (Mon Apr 2025 → Tue Sep 2025); BSE → Thursday (Sep 2025) |
| 35 | 5 | Table 1A #30 | Rollover week = Mon-Wed before last Thu | Corrected: Fri–Mon before last Tuesday (NSE) |
| 36 | 5 | Table 1F #131 | Max pain "Thursday = trade" | Corrected to Tuesday (NSE Nifty 50 weekly expiry) |
| 37 | 5 | Table 2C #28 | "Thursday, 2PM" for max pain gravity | Corrected to Tuesday |
| 38 | 5 | Table 2D #35 | Expiry day assignments all outdated | Updated to Tue=NSE Nifty 50, Thu=BSE Sensex (Sep 2025 change) |
| 39 | 5 | Table 2D #41 | "last Thursday" for monthly expiry | Corrected: NSE = last Tuesday; BSE = last Thursday |
| 40 | 5 | Table E3 | Title/structure built on Thursday expiry assumption | Reframed: rollover Fri–Mon; NSE expiry Tuesday; BSE Sensex Thursday |
| 41 | 5 | Table E5 May | "MSCI quarterly review" | Corrected to "MSCI Semi-Annual Index Review" (May/Nov = semi-annual; Feb/Aug = quarterly) |
| 42 | 5 | Table E5 Nov | "MSCI quarterly review" | Corrected to "MSCI Semi-Annual Index Review" |
| 43 | 5 | Table 3B #19 | ADR list included TTM | Removed TTM (Tata Motors delisted NYSE ADR Jan 2023) |
| 44 | 6 | Table 1F #137 | "FII Category I, II, III" | Corrected: Category III abolished by SEBI FPI Regs 2019; only Category I and II exist |
| 45 | 6 | Table 3B #17 | "FII Category I, II, III" | Corrected: Category I and II only |
| 46 | 6 | Table 1H #164 | Pharmexcil source = pharmexcil.org | Corrected to pharmexcil.com |
| 47 | 7 | Table 1E #103 | Formula used raw "OI"; MWPL basis = 20% free float | Corrected: FutEq OI (Oct 2025); MWPL = lower of 15% free float or 65×ADDV |
| 48 | 7 | Table 1E #104 | "Cannot open new positions during ban" | Corrected: post Dec 8 2025 rule — new positions allowed during ban if they reduce net FutEq OI by EOD; rollovers explicitly allowed |
| 49 | 7 | Table 3C #21 | Implied MWPL only checked post-market | Corrected: MWPL checked 4 random times intraday since Oct 2025; ban can trigger during live session |

*48 distinct errors corrected across 49 line-level edits (MWPL entry touched in passes 2 and 7).*

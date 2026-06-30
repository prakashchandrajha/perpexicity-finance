from __future__ import annotations

from typing import Any


def make_gold_rows(category: str, endpoint_url: str, payload: Any, observed_at: str) -> list[dict[str, Any]]:
    if category == "market_status":
        return market_status_rows(endpoint_url, payload, observed_at)
    if category == "indices":
        return index_rows(endpoint_url, payload, observed_at)
    if category == "option_chain":
        return option_chain_rows(endpoint_url, payload, observed_at)
    if category == "pre_open":
        return pre_open_rows(endpoint_url, payload, observed_at)
    if category == "live_analysis":
        return live_analysis_rows(endpoint_url, payload, observed_at)
    if category == "corporate":
        return event_rows(category, "event_risk", endpoint_url, payload, observed_at)
    if category in {"quotes", "exchange_communication", "market_activity"}:
        return event_rows(category, "market_context", endpoint_url, payload, observed_at)
    return []


def market_status_rows(endpoint_url: str, payload: Any, observed_at: str) -> list[dict[str, Any]]:
    rows = []
    for item in payload.get("marketState", []) if isinstance(payload, dict) else []:
        rows.append(
            {
                "category": "market_status",
                "signal_type": "risk_guard",
                "priority": 1,
                "payload": item,
                "source_endpoint": endpoint_url,
                "observed_at": observed_at,
            }
        )
    return rows


def index_rows(endpoint_url: str, payload: Any, observed_at: str) -> list[dict[str, Any]]:
    rows = []
    if not isinstance(payload, dict):
        return rows

    for item in payload.get("data", []):
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "category": "indices",
                "signal_type": "breadth",
                "index_name": item.get("index") or item.get("indexName"),
                "priority": 1,
                "payload": compact(item, ["index", "indexName", "last", "variation", "percentChange", "advances", "declines", "unchanged", "lastPrice", "pChange", "totalTradedVolume", "totalTradedValue"]),
                "source_endpoint": endpoint_url,
                "observed_at": observed_at,
            }
        )

    for item in payload.get("data", []):
        if not isinstance(item, dict) or not item.get("symbol"):
            continue
        rows.append(
            {
                "category": "indices",
                "signal_type": "constituent_pressure",
                "symbol": item.get("symbol"),
                "index_name": payload.get("metadata", {}).get("indexName"),
                "priority": 1,
                "payload": compact(item, ["symbol", "industry", "lastPrice", "change", "pChange", "totalTradedVolume", "totalTradedValue", "ffmc", "nearWKH", "nearWKL", "perChange30d", "perChange365d"]),
                "source_endpoint": endpoint_url,
                "observed_at": observed_at,
            }
        )
    return rows


def pre_open_rows(endpoint_url: str, payload: Any, observed_at: str) -> list[dict[str, Any]]:
    """Extract pre-open auction data — gap context and opening imbalance."""
    rows = []
    if not isinstance(payload, dict):
        return rows

    # Add a summary row with breadth
    summary = compact(payload, ["advances", "declines", "unchanged", "totalTradedVolume", "totalTradedValue", "totalmarketcap", "timestamp"])
    if summary:
        rows.append({
            "category": "pre_open",
            "signal_type": "breadth",
            "priority": 1,
            "payload": summary,
            "source_endpoint": endpoint_url,
            "observed_at": observed_at,
        })

    # Extract individual stock pre-open data
    for item in payload.get("data", []):
        if not isinstance(item, dict):
            continue
        metadata = item.get("metadata", {})
        detail = item.get("detail", {})
        if not isinstance(metadata, dict):
            continue
        symbol = metadata.get("symbol")
        row_payload = compact(metadata, [
            "symbol", "lastPrice", "change", "pChange", "previousClose",
            "iep", "iepTurnover", "finalQuantity", "year365High", "year365Low",
            "totalBuyQuantity", "totalSellQuantity",
        ])
        # Add the pre-open change percentage (the gap)
        if "pChange" in row_payload:
            row_payload["gap_pct"] = row_payload["pChange"]
        rows.append({
            "category": "pre_open",
            "signal_type": "gap_context",
            "symbol": symbol,
            "priority": 1,
            "payload": row_payload,
            "source_endpoint": endpoint_url,
            "observed_at": observed_at,
        })
    return rows


def live_analysis_rows(endpoint_url: str, payload: Any, observed_at: str) -> list[dict[str, Any]]:
    """Extract gainers, losers, and most active securities."""
    rows = []
    if not isinstance(payload, dict):
        return rows

    # Most active securities (has a simple "data" array)
    if isinstance(payload.get("data"), list) and payload["data"] and isinstance(payload["data"][0], dict):
        items = payload["data"]
        # Determine if this is most-active by value or volume from URL
        signal = "unusual_activity"
        if "value" in endpoint_url:
            signal = "cash_activity_value"
        elif "volume" in endpoint_url:
            signal = "cash_activity_volume"
        elif "gainers" in endpoint_url:
            signal = "momentum_gainer"
        elif "losers" in endpoint_url:
            signal = "momentum_loser"

        for item in items[:30]:
            rows.append({
                "category": "live_analysis",
                "signal_type": signal,
                "symbol": item.get("symbol"),
                "priority": 2,
                "payload": compact(item, [
                    "symbol", "series", "lastPrice", "change", "pChange",
                    "totalTradedVolume", "totalTradedValue", "previousClose",
                    "lastUpdateTime", "open", "high", "low",
                ]),
                "source_endpoint": endpoint_url,
                "observed_at": observed_at,
            })
        return rows

    # Gainers/Losers have nested sections: NIFTY, BANKNIFTY, FOSec, allSec, etc.
    for section_key in ["NIFTY", "BANKNIFTY", "FOSec", "allSec", "NIFTYNEXT50", "SecGtr20", "SecLwr20"]:
        section = payload.get(section_key, {})
        if not isinstance(section, dict):
            continue
        items = section.get("data", [])
        if not isinstance(items, list):
            continue

        signal = "momentum_gainer" if "gainers" in endpoint_url else "momentum_loser"

        for item in items[:20]:
            if not isinstance(item, dict):
                continue
            rows.append({
                "category": "live_analysis",
                "signal_type": signal,
                "symbol": item.get("symbol"),
                "index_name": section_key,
                "priority": 2,
                "payload": compact(item, [
                    "symbol", "series", "lastPrice", "change", "pChange",
                    "totalTradedVolume", "totalTradedValue", "previousClose",
                    "open", "high", "low",
                ]),
                "source_endpoint": endpoint_url,
                "observed_at": observed_at,
            })
    return rows


def option_chain_rows(endpoint_url: str, payload: Any, observed_at: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    records = payload.get("records", {})
    rows = []
    for item in records.get("data", [])[:300]:
        if not isinstance(item, dict):
            continue
        strike = item.get("strikePrice")
        rows.append(
            {
                "category": "option_chain",
                "signal_type": "option_flow",
                "index_name": records.get("underlyingValue"),
                "priority": 1,
                "payload": {
                    "strikePrice": strike,
                    "expiryDate": item.get("expiryDate"),
                    "CE": compact(item.get("CE", {}), ["openInterest", "changeinOpenInterest", "totalTradedVolume", "impliedVolatility", "lastPrice", "underlying"]),
                    "PE": compact(item.get("PE", {}), ["openInterest", "changeinOpenInterest", "totalTradedVolume", "impliedVolatility", "lastPrice", "underlying"]),
                },
                "source_endpoint": endpoint_url,
                "observed_at": observed_at,
            }
        )
    return rows


def event_rows(category: str, signal_type: str, endpoint_url: str, payload: Any, observed_at: str) -> list[dict[str, Any]]:
    rows = []
    records = []
    if isinstance(payload, dict):
        for key in ("data", "rows", "result", "circulars"):
            if isinstance(payload.get(key), list):
                records = payload[key]
                break
    elif isinstance(payload, list):
        records = payload

    for item in records[:100]:
        if isinstance(item, dict):
            rows.append(
                {
                    "category": category,
                    "signal_type": signal_type,
                    "symbol": item.get("symbol") or item.get("companySymbol"),
                    "priority": 2,
                    "payload": item,
                    "source_endpoint": endpoint_url,
                    "observed_at": observed_at,
                }
            )
    return rows


def compact(payload: Any, keys: list[str]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    return {key: payload.get(key) for key in keys if key in payload}



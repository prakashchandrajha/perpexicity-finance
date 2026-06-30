from __future__ import annotations

from typing import Any


def make_gold_rows(category: str, endpoint_url: str, payload: Any, observed_at: str) -> list[dict[str, Any]]:
    if category == "market_status":
        return market_status_rows(endpoint_url, payload, observed_at)
    if category == "indices":
        return index_rows(endpoint_url, payload, observed_at)
    if category == "option_chain":
        return option_chain_rows(endpoint_url, payload, observed_at)
    if category == "corporate":
        return event_rows(category, "event_risk", endpoint_url, payload, observed_at)
    if category in {"live_analysis", "pre_open", "quotes", "exchange_communication"}:
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


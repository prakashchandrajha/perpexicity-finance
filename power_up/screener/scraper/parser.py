from __future__ import annotations

import re
from typing import Any

from models.schema import CompanySnapshot, RawScreenerResult, ScreenCandidate


def parse_number(value: str | None) -> float | None:
    if not value:
        return None
    cleaned = value.replace(",", "").replace("%", "").replace("Cr.", "").replace("cr", "")
    match = re.search(r"-?\d+(\.\d+)?", cleaned)
    return float(match.group(0)) if match else None


def first_metric(row: dict[str, Any], names: list[str]) -> str | None:
    lowered = {str(key).strip().lower(): value for key, value in row.items()}
    for name in names:
        for key, value in lowered.items():
            if name.lower() in key:
                return str(value)
    return None


def symbol_from_href(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"/company/([^/]+)/?", value)
    return match.group(1).upper() if match else None


def parse_screen_candidates(raw: RawScreenerResult) -> list[ScreenCandidate]:
    if not raw.tables:
        return []

    rows = raw.tables[0].get("rows", [])
    candidates: list[ScreenCandidate] = []
    for row in rows[:50]:
        name = first_metric(row, ["name", "company"]) or "Unknown"
        # Skip header rows that leaked through DOM extraction
        if name.strip().lower() in ("name", "company", "unknown", "s.no."):
            continue
        symbol = first_metric(row, ["symbol", "nse code", "bse code"]) or symbol_from_href(row.get("_href"))
        candidate = ScreenCandidate(
            name=name,
            symbol=symbol,
            metrics={str(key): str(value) for key, value in row.items()},
        )
        candidates.append(candidate)
    return candidates


def parse_company_snapshot(raw: RawScreenerResult, symbol: str) -> CompanySnapshot:
    return CompanySnapshot(
        symbol=symbol.upper(),
        name=raw.title,
        ratios=raw.ratios,
        financial_tables=raw.tables,
    )

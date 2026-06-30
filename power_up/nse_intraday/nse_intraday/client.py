from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import urlencode, quote

import requests

from .config import BASE_URL, DEFAULT_TIMEOUT, USER_AGENT
from .endpoints import EndpointSeed

_MIN_REQUEST_INTERVAL = 0.4  # seconds between NSE requests


class NSEClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept": "application/json,text/plain,*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": BASE_URL + "/",
            }
        )
        self._bootstrapped = False
        self._last_request_time = 0.0

    def bootstrap(self, force: bool = False) -> None:
        if self._bootstrapped and not force:
            return
        response = self.session.get(BASE_URL, timeout=DEFAULT_TIMEOUT)
        response.raise_for_status()
        self._bootstrapped = True

    def _throttle(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < _MIN_REQUEST_INTERVAL:
            time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()

    def build_url(self, path: str, params: dict[str, str] | None = None) -> str:
        url = BASE_URL + path
        if params:
            return f"{url}?{urlencode(params, quote_via=quote)}"
        return url

    def fetch_json(self, path: str, params: dict[str, str] | None = None) -> tuple[str, Any]:
        self.bootstrap()
        url = self.build_url(path, params)
        self._throttle()
        response = self.session.get(url, timeout=DEFAULT_TIMEOUT)

        # Retry once with fresh cookies on 403
        if response.status_code == 403:
            self.bootstrap(force=True)
            self._throttle()
            response = self.session.get(url, timeout=DEFAULT_TIMEOUT)

        response.raise_for_status()
        try:
            return url, response.json()
        except json.JSONDecodeError as exc:
            raise ValueError(f"NSE returned non-JSON for {url}") from exc

    def probe(self, seed: EndpointSeed) -> dict[str, Any]:
        url, payload = self.fetch_json(seed.path, seed.params)
        return {
            "category": seed.category,
            "path": seed.path,
            "url": url,
            "purpose": seed.purpose,
            "params": seed.params,
            "update_frequency": seed.update_frequency,
            "bot_value": seed.bot_value,
            "priority": seed.priority,
            "structure": summarize_json(payload),
        }


def summarize_json(payload: Any, *, max_items: int = 5) -> dict[str, Any]:
    if isinstance(payload, dict):
        return {
            "type": "object",
            "keys": sorted(str(key) for key in payload.keys()),
            "children": {
                str(key): summarize_json(value, max_items=max_items)
                for key, value in list(payload.items())[:max_items]
            },
        }
    if isinstance(payload, list):
        sample = payload[:max_items]
        return {
            "type": "array",
            "length": len(payload),
            "sample": [summarize_json(item, max_items=max_items) for item in sample],
        }
    return {"type": type(payload).__name__, "example": payload}


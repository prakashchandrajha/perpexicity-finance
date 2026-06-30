from __future__ import annotations

import re
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import requests

from .client import summarize_json
from .config import BASE_URL, DEFAULT_TIMEOUT, MAX_DEFAULT_DISCOVERY_PAGES, SEED_PAGES, USER_AGENT
from .taxonomy import EndpointProfile, endpoint_param_names, endpoint_params, endpoint_path, profile_endpoint

API_RE = re.compile(r"(/api/[A-Za-z0-9_./?=&%+\-:{}[\],$]+)")
ASSET_EXTENSIONS = (".js", ".mjs")
SKIP_LINK_PARTS = ("#", "javascript:", "mailto:", "tel:", ".pdf", ".zip", ".csv", ".xls", ".xlsx")


@dataclass
class DiscoveredAPI:
    source_page: str
    url: str
    method: str = "GET"
    status: int | None = None
    structure: dict | None = None
    discovered_from: str | None = None
    profile: EndpointProfile = field(default_factory=lambda: profile_endpoint(""))

    @property
    def path(self) -> str:
        return endpoint_path(self.url)

    @property
    def params(self) -> dict[str, str]:
        return endpoint_params(self.url)

    @property
    def parameter_names(self) -> list[str]:
        return endpoint_param_names(self.url)


@dataclass
class PageScan:
    page_url: str
    apis: list[DiscoveredAPI]
    internal_links: list[str]
    assets: list[str]


ProgressCallback = Callable[[str, int, int, int, int, int], None]
PageScanCallback = Callable[[PageScan], None]


class NSELinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for key, value in attrs:
            if key in {"href", "src"} and value:
                self.references.append((tag, value))


def discover_static(page_url: str, *, include_assets: bool = True) -> list[DiscoveredAPI]:
    return scan_page_static(page_url, include_assets=include_assets).apis


def scan_page_static(page_url: str, *, include_assets: bool = True) -> PageScan:
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,*/*"}
    response = requests.get(page_url, headers=headers, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()

    api_sources: dict[str, str] = {}
    for api_url in extract_api_urls(response.text, page_url):
        api_sources[api_url] = page_url

    parser = NSELinkParser()
    parser.feed(response.text)

    assets: set[str] = set()
    internal_links: set[str] = set()
    for tag, value in parser.references:
        absolute = urljoin(page_url, value)
        if not is_nse_url(absolute):
            continue
        if tag == "script" and urlparse(absolute).path.endswith(ASSET_EXTENSIONS):
            assets.add(strip_fragment(absolute))
        elif tag == "link" and urlparse(absolute).path.endswith(ASSET_EXTENSIONS):
            assets.add(strip_fragment(absolute))
        elif tag == "a":
            normalized = normalize_page_link(absolute)
            if normalized:
                internal_links.add(normalized)

    if include_assets:
        for asset_url in sorted(assets):
            try:
                asset_response = requests.get(asset_url, headers=headers, timeout=DEFAULT_TIMEOUT)
                asset_response.raise_for_status()
            except Exception:
                continue
            for api_url in extract_api_urls(asset_response.text, asset_url):
                api_sources.setdefault(api_url, asset_url)

    apis = [
        DiscoveredAPI(
            source_page=page_url,
            url=url,
            discovered_from=source,
            profile=profile_endpoint(url),
        )
        for url, source in sorted(api_sources.items())
    ]
    return PageScan(page_url=page_url, apis=apis, internal_links=sorted(internal_links), assets=sorted(assets))


def discover_site_static(
    seed_pages: list[str] | None = None,
    max_pages: int = MAX_DEFAULT_DISCOVERY_PAGES,
    *,
    include_assets: bool = True,
    progress: ProgressCallback | None = None,
    on_scan: PageScanCallback | None = None,
) -> tuple[list[DiscoveredAPI], list[str]]:
    normalized_seeds = [page for page in (normalize_page_link(url) for url in (seed_pages or SEED_PAGES)) if page]
    queue = deque(normalized_seeds)
    queued: set[str] = set(normalized_seeds)
    visited: set[str] = set()
    all_apis: dict[tuple[str, str], DiscoveredAPI] = {}

    while queue and len(visited) < max_pages:
        page_url = normalize_page_link(queue.popleft())
        if page_url:
            queued.discard(page_url)
        if not page_url or page_url in visited:
            continue
        visited.add(page_url)
        try:
            scan = scan_page_static(page_url, include_assets=include_assets)
        except Exception as exc:
            if progress:
                progress(page_url, len(visited), max_pages, len(queue), 0, len(all_apis))
                print(f"  failed: {exc}")
            continue

        for api in scan.apis:
            all_apis[(api.source_page, api.url)] = api

        if on_scan:
            on_scan(scan)

        for link in scan.internal_links:
            if link not in visited and link not in queued and is_discovery_page(link):
                queue.append(link)
                queued.add(link)

        if progress:
            progress(page_url, len(visited), max_pages, len(queue), len(scan.apis), len(all_apis))

    return list(all_apis.values()), sorted(visited)


def discover_with_playwright(page_url: str, wait_ms: int = 8000) -> list[DiscoveredAPI]:
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise RuntimeError("Install playwright and run `python -m playwright install chromium`.") from exc

    discovered: dict[str, DiscoveredAPI] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=USER_AGENT)

        def on_response(response) -> None:
            url = response.url
            if "/api/" not in url or "nseindia.com" not in urlparse(url).netloc:
                return
            item = DiscoveredAPI(
                source_page=page_url,
                url=url,
                method=response.request.method,
                status=response.status,
                discovered_from="browser_network",
                profile=profile_endpoint(url),
            )
            try:
                item.structure = summarize_json(response.json())
            except Exception:
                item.structure = None
            discovered[url] = item

        page.on("response", on_response)
        page.goto(page_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(wait_ms)
        browser.close()

    return list(discovered.values())


def extract_api_urls(text: str, base_url: str) -> set[str]:
    urls: set[str] = set()
    for match in API_RE.findall(text):
        candidate = clean_api_match(match)
        if candidate:
            urls.add(urljoin(BASE_URL if candidate.startswith("/api/") else base_url, candidate))
    return urls


def clean_api_match(match: str) -> str | None:
    candidate = match.replace("\\u0026", "&").replace("&amp;", "&")
    candidate = candidate.strip("'\"` ,;)]}")
    candidate = candidate.split("\\", 1)[0]
    candidate = candidate.split("#", 1)[0]
    if not candidate.startswith("/api/"):
        return None
    if "${" in candidate or "}" in candidate:
        candidate = candidate.split("${", 1)[0].rstrip("?&=/")
    return candidate


def is_nse_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and parsed.netloc.endswith("nseindia.com")


def strip_fragment(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(fragment="").geturl()


def normalize_page_link(url: str) -> str | None:
    if any(part in url.lower() for part in SKIP_LINK_PARTS):
        return None
    if not is_nse_url(url):
        return None
    parsed = urlparse(strip_fragment(url))
    if parsed.path.startswith("/api/"):
        return None
    if parsed.path.endswith(ASSET_EXTENSIONS):
        return None
    return parsed._replace(query="").geturl()


def is_discovery_page(url: str) -> bool:
    path = urlparse(url).path
    if path in {"", "/"}:
        return True
    interesting_prefixes = (
        "/market-data",
        "/option-chain",
        "/companies-listing",
        "/resources",
        "/regulations",
        "/products-services",
        "/national-commodity",
    )
    return path.startswith(interesting_prefixes)

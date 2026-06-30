#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from nse_intraday.client import NSEClient
from nse_intraday.config import MAX_DEFAULT_DISCOVERY_PAGES, SEED_PAGES
from nse_intraday.discovery import discover_site_static, discover_static, discover_with_playwright
from nse_intraday.endpoints import CATALOG, iter_default_collect, iter_default_probe
from nse_intraday.gold import make_gold_rows
from nse_intraday.storage import Store
from nse_intraday.taxonomy import profile_endpoint


def cmd_catalog() -> None:
    store = Store()
    for seed in CATALOG:
        store.save_catalog_seed(seed)
        params = f"?{json.dumps(seed.params, sort_keys=True)}" if seed.params else ""
        print(f"[P{seed.priority}] {seed.category}: {seed.path}{params}")
        print(f"  purpose: {seed.purpose}")
        print(f"  bot: {seed.bot_value}")
    print(f"\nseed endpoints: {len(CATALOG)}")


def cmd_pages() -> None:
    for page in SEED_PAGES:
        print(page)
    print(f"\nseed pages: {len(SEED_PAGES)}")


def cmd_probe() -> None:
    client = NSEClient()
    store = Store()
    for seed in iter_default_probe():
        store.save_catalog_seed(seed)
        try:
            result = client.probe(seed)
            store.save_observation(result["url"], None, 200, result["structure"])
            print(f"OK {result['url']}")
            print(f"  keys: {result['structure'].get('keys', result['structure'].get('type'))}")
        except Exception as exc:
            store.save_observation(client.build_url(seed.path, seed.params), None, None, {"error": str(exc)})
            print(f"FAIL {seed.path}: {exc}")


def cmd_collect(gold_only: bool) -> None:
    client = NSEClient()
    store = Store()
    total_gold = 0
    for seed in iter_default_collect():
        try:
            url, payload = client.fetch_json(seed.path, seed.params)
            observed_at = store.save_raw(seed.category, url, payload)
            rows = make_gold_rows(seed.category, url, payload, observed_at)
            store.save_gold(rows)
            total_gold += len(rows)
            if gold_only:
                print(f"gold {len(rows):>4} rows <- {url}")
            else:
                print(json.dumps({"url": url, "gold_rows": len(rows)}, ensure_ascii=False))
        except Exception as exc:
            print(f"FAIL {seed.path}: {exc}")
    print(f"saved {total_gold} gold rows")


def cmd_discover_page(page_url: str, browser: bool) -> None:
    store = Store()
    if browser:
        discovered = discover_with_playwright(page_url)
    else:
        discovered = discover_static(page_url)

    for item in discovered:
        store.save_discovered_api(item)
        store.save_observation(item.url, item.source_page, item.status, item.structure)
        print(f"{item.method} {item.url}")
        print(f"  category: {item.profile.category} / {item.profile.signal_type}")
        print(f"  params: {', '.join(item.parameter_names) if item.parameter_names else '-'}")
        print(f"  frequency: {item.profile.update_frequency}")
        print(f"  bot: {item.profile.bot_value}")
        if item.status:
            print(f"  status: {item.status}")
        if item.structure:
            print(f"  structure: {json.dumps(item.structure)[:300]}")


def cmd_discover_site(max_pages: int, include_assets: bool, fresh: bool) -> None:
    store = Store()
    if fresh:
        store.reset_all()
        print("Reset data/nse_intraday.db before discovery.", flush=True)

    def show_progress(page_url: str, visited: int, target: int, queued: int, page_apis: int, total_apis: int) -> None:
        print(
            f"[{visited}/{target}] apis={page_apis} total={total_apis} queue={queued} {page_url}",
            flush=True,
        )

    print(
        f"Starting NSE discovery: max_pages={max_pages}, assets={'on' if include_assets else 'off'}",
        flush=True,
    )

    def save_scan(scan) -> None:
        for item in scan.apis:
            store.save_discovered_api(item)
            store.save_observation(item.url, item.source_page, item.status, item.structure)

    discovered, visited_pages = discover_site_static(
        max_pages=max_pages,
        include_assets=include_assets,
        progress=show_progress,
        on_scan=save_scan,
    )

    by_category: dict[str, int] = {}
    for item in discovered:
        by_category[item.profile.category] = by_category.get(item.profile.category, 0) + 1

    print(f"visited pages: {len(visited_pages)}")
    print(f"discovered api page-usages: {len(discovered)}")
    for category, count in sorted(by_category.items(), key=lambda pair: (-pair[1], pair[0])):
        print(f"  {category}: {count}")


def cmd_classify(url_or_path: str) -> None:
    profile = profile_endpoint(url_or_path)
    print(f"category: {profile.category}")
    print(f"signal_type: {profile.signal_type}")
    print(f"purpose: {profile.purpose}")
    print(f"update_frequency: {profile.update_frequency}")
    print(f"bot_value: {profile.bot_value}")
    print(f"priority: {profile.priority}")


def cmd_reclassify_catalog() -> None:
    store = Store()
    counts = store.reclassify_catalog()
    for category, count in sorted(counts.items(), key=lambda pair: (-pair[1], pair[0])):
        print(f"{category}: {count}")


def cmd_catalog_summary() -> None:
    store = Store()
    for category, count in store.catalog_summary():
        print(f"{category}: {count}")


def cmd_reset_db() -> None:
    Store().reset_all()
    print("Reset data/nse_intraday.db")


def cmd_catalog_export(output: str | None, limit: int | None) -> None:
    store = Store()
    rows = store.catalog_rows(limit)
    lines = ["# NSE API Catalog", ""]
    current_category = None
    for row in rows:
        if row["category"] != current_category:
            current_category = row["category"]
            lines.extend(["", f"## {current_category}", ""])
            lines.append("| Endpoint | Params | Signal | Frequency | Priority | Collect | Used by | Bot value |")
            lines.append("|---|---|---|---|---:|---|---|---|")
        params = json.loads(row["params_json"] or "{}")
        params_text = ", ".join(f"{key}={value}" for key, value in params.items()) or "-"
        source = row["source_page"] or "seed"
        collect = "yes" if row["collect_by_default"] else "no"
        lines.append(
            f"| `{row['method'] or 'GET'} {row['path']}` | {params_text} | "
            f"{row['signal_type'] or '-'} | {row['update_frequency']} | {row['priority']} | "
            f"{collect} | {source} | {row['bot_value']} |"
        )

    content = "\n".join(lines).strip() + "\n"
    if output:
        Path(output).write_text(content, encoding="utf-8")
        print(f"wrote {output}")
    else:
        print(content)


def cmd_gold(limit: int) -> None:
    store = Store()
    for row in store.latest_gold(limit):
        payload = json.loads(row["payload_json"])
        label = row["symbol"] or row["index_name"] or "-"
        print(f"[P{row['priority']}] {row['category']} / {row['signal_type']} / {label}")
        print(f"  source: {row['source_endpoint']}")
        print(f"  payload: {json.dumps(payload, ensure_ascii=False)[:500]}")


def main() -> None:
    parser = argparse.ArgumentParser(description="NSE Intraday API catalog and gold-data collector")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("catalog", help="Print and save the seed NSE API catalog")
    subparsers.add_parser("pages", help="Print the NSE public page seeds used for discovery")
    subparsers.add_parser("probe", help="Call seed endpoints and save response structures")

    collect_parser = subparsers.add_parser("collect", help="Collect NSE public data into SQLite")
    collect_parser.add_argument("--gold-only", action="store_true", help="Print compact gold collection output")

    discover_parser = subparsers.add_parser("discover-page", help="Discover API calls used by an NSE page")
    discover_parser.add_argument("page_url")
    discover_parser.add_argument("--browser", action="store_true", help="Use Playwright network capture")

    site_parser = subparsers.add_parser("discover-site", help="Static-crawl NSE seed pages and discover API references")
    site_parser.add_argument("--max-pages", type=int, default=MAX_DEFAULT_DISCOVERY_PAGES)
    site_parser.add_argument("--no-assets", action="store_true", help="Skip JS asset scanning for a faster shallow crawl")
    site_parser.add_argument("--fresh", action="store_true", help="Clear existing SQLite crawl data before discovery")

    classify_parser = subparsers.add_parser("classify", help="Classify one NSE API URL/path into bot taxonomy")
    classify_parser.add_argument("url_or_path")

    subparsers.add_parser("reclassify-catalog", help="Re-apply the latest taxonomy to saved discovered endpoints")
    subparsers.add_parser("catalog-summary", help="Summarize saved endpoint catalog by category")
    subparsers.add_parser("reset-db", help="Clear all SQLite catalog, observation, raw, and gold data")

    export_parser = subparsers.add_parser("catalog-export", help="Export saved endpoint catalog as Markdown")
    export_parser.add_argument("--output", help="Optional output markdown file")
    export_parser.add_argument("--limit", type=int, help="Optional row limit")

    gold_parser = subparsers.add_parser("gold", help="Show latest bot-ready gold rows")
    gold_parser.add_argument("--limit", type=int, default=30)

    args = parser.parse_args()
    if args.command == "catalog":
        cmd_catalog()
    elif args.command == "pages":
        cmd_pages()
    elif args.command == "probe":
        cmd_probe()
    elif args.command == "collect":
        cmd_collect(args.gold_only)
    elif args.command == "discover-page":
        cmd_discover_page(args.page_url, args.browser)
    elif args.command == "discover-site":
        cmd_discover_site(args.max_pages, not args.no_assets, args.fresh)
    elif args.command == "classify":
        cmd_classify(args.url_or_path)
    elif args.command == "reclassify-catalog":
        cmd_reclassify_catalog()
    elif args.command == "catalog-summary":
        cmd_catalog_summary()
    elif args.command == "reset-db":
        cmd_reset_db()
    elif args.command == "catalog-export":
        cmd_catalog_export(args.output, args.limit)
    elif args.command == "gold":
        cmd_gold(args.limit)


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from pathlib import Path

from loguru import logger

from config import DEFAULT_SCREENS, PHASE_SCREEN_NAMES, SCREENER_BASE_URL
from models.schema import Phase, PhaseOutput, ScreenerJob
from scraper.extension_client import ScreenerExtensionClient
from scraper.parser import parse_company_snapshot, parse_screen_candidates
from signals.scoring import score_candidate, score_company
from storage.save import save_phase_output


def run_screen(screen_name: str, phase: Phase, context: str | None) -> Path:
    screen = DEFAULT_SCREENS[screen_name]
    job = ScreenerJob(job_type="screen", phase=phase, screen_name=screen_name, query=screen["query"], context=context)
    raw = ScreenerExtensionClient().submit_and_wait(job)
    candidates = [score_candidate(candidate) for candidate in parse_screen_candidates(raw)]
    output = PhaseOutput(phase=phase, context=context, screen_candidates=candidates, raw_result=raw)
    return save_phase_output(output, screen_name)


def run_company(symbol: str, phase: Phase, context: str | None) -> Path:
    job = ScreenerJob(job_type="company", phase=phase, symbol=symbol.upper(), context=context)
    raw = ScreenerExtensionClient().submit_and_wait(job)
    snapshot = score_company(parse_company_snapshot(raw, symbol))
    output = PhaseOutput(phase=phase, context=context, company_snapshot=snapshot, raw_result=raw)
    return save_phase_output(output, symbol)


def print_screens() -> None:
    for name, screen in DEFAULT_SCREENS.items():
        print(f"{name}: {screen['description']}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Screener.in intelligence layer for trading bots")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list-screens")

    screen_parser = subparsers.add_parser("screen")
    screen_parser.add_argument("name", choices=sorted(DEFAULT_SCREENS))
    screen_parser.add_argument("--phase", default="pre_market", choices=["pre_market", "live_market", "post_market"])
    screen_parser.add_argument("--context")

    company_parser = subparsers.add_parser("company")
    company_parser.add_argument("symbol")
    company_parser.add_argument("--phase", default="pre_market", choices=["pre_market", "live_market", "post_market"])
    company_parser.add_argument("--context")

    phase_parser = subparsers.add_parser("phase")
    phase_parser.add_argument("phase", choices=["pre_market", "live_market", "post_market"])
    phase_parser.add_argument("--context")

    args = parser.parse_args()

    if args.command == "list-screens":
        print_screens()
        return

    logger.info("Source: {}", SCREENER_BASE_URL)
    if args.command == "screen":
        path = run_screen(args.name, args.phase, args.context)
        print(f"SAVED TO: {path}")
    elif args.command == "company":
        path = run_company(args.symbol, args.phase, args.context)
        print(f"SAVED TO: {path}")
    elif args.command == "phase":
        saved = []
        for screen_name in PHASE_SCREEN_NAMES[args.phase]:
            saved.append(run_screen(screen_name, args.phase, args.context))
        print("SAVED:")
        for path in saved:
            print(path)


if __name__ == "__main__":
    main()


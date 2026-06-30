import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

from scraper.extension_client import TrendlyneExtensionClient


def has_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def extract_trendlyne_signals(response: str) -> dict:
    """Convert MarketMind prose into coarse bot-readable institutional context."""
    text = response.lower()
    flags: list[str] = []

    delivery_trend = "unknown"
    if has_any(text, [
        "delivery volume increased",
        "higher delivery",
        "delivery buying",
        "delivery accumulation",
        "strong delivery",
        "rising delivery",
    ]):
        delivery_trend = "supportive"
        flags.append("delivery_support")
    elif has_any(text, [
        "delivery volume declined",
        "lower delivery",
        "weak delivery",
        "delivery selling",
        "falling delivery",
    ]):
        delivery_trend = "weak"
        flags.append("delivery_weak")

    block_deal_signal = "unknown"
    if "block deal" in text or "bulk deal" in text:
        if has_any(text, ["no block", "no bulk", "no recent block", "not found", "none reported"]):
            block_deal_signal = "none_reported"
        else:
            block_deal_signal = "present"
            flags.append("block_or_bulk_deal")

    fii_signal = "unknown"
    if has_any(text, [
        "fii holding increased",
        "foreign institutional holding increased",
        "fpi holding increased",
        "fpis increased",
        "fii increased stake",
    ]):
        fii_signal = "supportive"
        flags.append("fii_support")
    elif has_any(text, [
        "fii holding declined",
        "foreign institutional holding declined",
        "fpi holding declined",
        "fpis reduced",
        "fii reduced stake",
    ]):
        fii_signal = "weak"
        flags.append("fii_weak")

    institutional_bias = "mixed"
    supportive_count = sum(1 for item in [delivery_trend, fii_signal] if item == "supportive")
    weak_count = sum(1 for item in [delivery_trend, fii_signal] if item == "weak")
    if block_deal_signal == "present":
        institutional_bias = "manual_review"
    elif supportive_count > weak_count:
        institutional_bias = "supportive"
    elif weak_count > supportive_count:
        institutional_bias = "weak"
    elif delivery_trend == "unknown" and fii_signal == "unknown" and block_deal_signal == "unknown":
        institutional_bias = "unknown"

    return {
        "delivery_trend": delivery_trend,
        "block_deal_signal": block_deal_signal,
        "fii_signal": fii_signal,
        "institutional_bias": institutional_bias,
        "flags": sorted(set(flags)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Trendlyne MarketMind AI Integration")
    parser.add_argument("ticker", help="Stock ticker (e.g. RELIANCE.NS)")
    parser.add_argument("--query", required=True, help="Question to ask MarketMind, e.g. 'Any insider buying?'")

    args = parser.parse_args()

    logger.info(f"Starting Trendlyne Agent for {args.ticker}...")
    client = TrendlyneExtensionClient()

    try:
        response = client.ask_marketmind(args.ticker, args.query)
        structured_context = extract_trendlyne_signals(response)
        logger.success(f"\n--- TRENDLYNE MARKETMIND AI RESPONSE ---\n{response}\n")
        logger.info(f"Structured context: {structured_context}")

        root_dir = Path(__file__).resolve().parent
        date_str = datetime.now().strftime("%Y-%m-%d")
        data_dir = root_dir / "data" / date_str
        data_dir.mkdir(parents=True, exist_ok=True)

        file_path = data_dir / f"marketmind_{args.ticker.replace('.NS', '').replace('.BO', '')}.json"

        output = {
            "ticker": args.ticker,
            "timestamp": datetime.now().isoformat(),
            "query": args.query,
            "structured_context": structured_context,
            "response": response,
        }

        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(output, file, indent=2, ensure_ascii=False)

        logger.info(f"Saved MarketMind response to {file_path}")
        print(f"TRENDLYNE_DATA_FILE={file_path}")

    except Exception as exc:
        logger.error(f"Failed to query Trendlyne: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
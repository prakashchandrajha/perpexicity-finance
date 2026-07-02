import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from loguru import logger

from scraper.extension_client import TrendlyneExtensionClient


def has_any(text: str, terms: list[str]) -> bool:
    return any(term in text for term in terms)


def extract_trendlyne_signals(response: str) -> dict:
    """Convert MarketMind prose into coarse bot-readable institutional context including DVM scores and broker targets."""
    text = response.lower()
    flags: list[str] = []

    durability = "unknown"
    valuation = "unknown"
    momentum = "unknown"
    broker_target_upside = "unknown"
    insider_signal = "unknown"

    # DVM Regex or keyword extract
    d_match = re.search(r"durability(?: score)?\s*(?:is|of|:|—|-)?\s*(\d{1,3})", text)
    if d_match:
        durability = f"{d_match.group(1)}/100"
        if int(d_match.group(1)) >= 55:
            flags.append("high_durability")
        elif int(d_match.group(1)) < 35:
            flags.append("low_durability")

    v_match = re.search(r"valuation(?: score)?\s*(?:is|of|:|—|-)?\s*(\d{1,3})", text)
    if v_match:
        valuation = f"{v_match.group(1)}/100"

    m_match = re.search(r"momentum(?: score)?\s*(?:is|of|:|—|-)?\s*(\d{1,3})", text)
    if m_match:
        momentum = f"{m_match.group(1)}/100"
        if int(m_match.group(1)) >= 60:
            flags.append("strong_momentum")

    if has_any(text, ["broker upgrade", "target price upgrade", "upside", "buy rating", "outperform"]):
        broker_target_upside = "positive"
        flags.append("broker_upgrade")
    elif has_any(text, ["broker downgrade", "target price downgrade", "downside", "sell rating", "underperform"]):
        broker_target_upside = "negative"
        flags.append("broker_downgrade")

    if has_any(text, ["insider buying", "insider bought", "promoter buying", "promoter increased"]):
        insider_signal = "buying"
        flags.append("insider_accumulation")
    elif has_any(text, ["insider selling", "insider sold", "promoter selling", "promoter reduced"]):
        insider_signal = "selling"
        flags.append("insider_selling")

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
    supportive_count = sum(1 for item in [delivery_trend, fii_signal, broker_target_upside, insider_signal] if item in ["supportive", "positive", "buying"])
    weak_count = sum(1 for item in [delivery_trend, fii_signal, broker_target_upside, insider_signal] if item in ["weak", "negative", "selling"])
    if block_deal_signal == "present":
        institutional_bias = "manual_review"
    elif supportive_count > weak_count:
        institutional_bias = "supportive"
    elif weak_count > supportive_count:
        institutional_bias = "weak"
    elif delivery_trend == "unknown" and fii_signal == "unknown" and block_deal_signal == "unknown" and durability == "unknown":
        institutional_bias = "unknown"

    return {
        "durability_score": durability,
        "valuation_score": valuation,
        "momentum_score": momentum,
        "broker_target_upside": broker_target_upside,
        "insider_signal": insider_signal,
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
        response_data = client.ask_marketmind(args.ticker, args.query)
        if isinstance(response_data, dict):
            raw_text = response_data.get("text", "")
            tables = response_data.get("tables", [])
            response_str = f"{raw_text}\n\nExtracted {len(tables)} tables."
        else:
            raw_text = str(response_data)
            tables = []
            response_str = raw_text

        structured_context = extract_trendlyne_signals(raw_text)
        logger.success(f"\n--- TRENDLYNE DOM EXTRACT ---\n{response_str}\n")
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
            "response": response_str,
            "tables": tables,
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
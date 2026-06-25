from loguru import logger
from models.schema import (
    QuoteData,
    ProfileData,
    EarningsEntry,
    AnalystDocument,
    TickerSnapshot,
)
from datetime import datetime


class FinanceExtractor:
    """Converts raw API response dicts into structured TickerSnapshot."""

    def extract(self, ticker: str, raw_api_data: dict, mode: str = "all") -> TickerSnapshot:
        """
        Extracts structured data from the raw API payload.
        If mode == 'live', heavy datasets like financials and earnings are skipped.
        """
        snapshot = TickerSnapshot(
            ticker=ticker,
            scraped_at=datetime.utcnow().isoformat(),
            source_url=f"https://www.perplexity.ai/finance/{ticker}",
            raw_api=raw_api_data,
        )

        # We always want profile and documents for narrative
        snapshot.profile = self._extract_profile(ticker, raw_api_data)
        snapshot.documents = self._extract_documents(ticker, raw_api_data)

        # For pre and post market, get everything
        if mode != "live":
            snapshot.quote = self._extract_quote(ticker, raw_api_data)
            snapshot.earnings = self._extract_earnings(ticker, raw_api_data)
            annual, quarterly = self._extract_financials(ticker, raw_api_data)
            snapshot.financials_annual = annual
            snapshot.financials_quarterly = quarterly
        else:
            logger.debug(f"Live mode: skipped parsing quote and financials for {ticker}")

        return snapshot

    def _find_api(self, api_data: dict, keyword: str) -> dict | list | None:
        """Find an API response by keyword in the key name."""
        for key, value in api_data.items():
            if keyword in key:
                return value
        return None

    def _extract_quote(self, ticker: str, api_data: dict) -> QuoteData | None:
        raw = self._find_api(api_data, f"quote/{ticker}")
        if not raw or not isinstance(raw, dict):
            logger.warning(f"No quote data found for {ticker}")
            return None

        try:
            return QuoteData(
                symbol=raw.get("symbol", ticker),
                name=raw.get("name", ""),
                price=raw.get("price", 0.0),
                change=raw.get("change", 0.0),
                changes_percentage=raw.get("changesPercentage", 0.0),
                day_low=raw.get("dayLow", 0.0),
                day_high=raw.get("dayHigh", 0.0),
                year_low=raw.get("yearLow", 0.0),
                year_high=raw.get("yearHigh", 0.0),
                market_cap=raw.get("marketCap"),
                volume=raw.get("volume"),
                avg_volume=raw.get("avgVolume"),
                open=raw.get("open"),
                previous_close=raw.get("previousClose"),
                eps=raw.get("eps"),
                pe=raw.get("pe"),
                exchange=raw.get("exchange", ""),
                currency=raw.get("currency", "USD"),
                is_market_open=raw.get("isMarketOpen", False),
                dividend_yield_ttm=raw.get("dividendYieldTTM"),
                price_avg_50=raw.get("priceAvg50"),
                price_avg_200=raw.get("priceAvg200"),
            )
        except Exception as e:
            logger.error(f"Failed to parse quote: {e}")
            return None

    def _extract_profile(self, ticker: str, api_data: dict) -> ProfileData | None:
        raw = self._find_api(api_data, f"profile/{ticker}")
        if not raw or not isinstance(raw, dict):
            logger.warning(f"No profile data found for {ticker}")
            return None

        try:
            return ProfileData(
                symbol=raw.get("symbol", ticker),
                company_name=raw.get("companyName", ""),
                industry=raw.get("industry"),
                sector=raw.get("sector"),
                description=raw.get("description"),
                website=raw.get("website"),
                ceo=raw.get("ceo"),
                country=raw.get("country"),
                employees=raw.get("fullTimeEmployees"),
                exchange=raw.get("exchangeShortName"),
                isin=raw.get("isin"),
            )
        except Exception as e:
            logger.error(f"Failed to parse profile: {e}")
            return None

    def _extract_earnings(
        self, ticker: str, api_data: dict
    ) -> list[EarningsEntry]:
        raw = self._find_api(api_data, f"earnings/{ticker}")
        if not raw:
            return []

        entries = raw if isinstance(raw, list) else []
        result = []
        for item in entries[:8]:  # Last 8 quarters
            try:
                result.append(
                    EarningsEntry(
                        date=item.get("date", ""),
                        revenue=item.get("revenue"),
                        revenue_estimated=item.get("revenueEstimated"),
                        eps=item.get("eps"),
                        eps_estimated=item.get("epsEstimated"),
                    )
                )
            except Exception:
                continue

        logger.info(f"Extracted {len(result)} earnings entries for {ticker}")
        return result

    def _extract_documents(
        self, ticker: str, api_data: dict
    ) -> list[AnalystDocument]:
        raw = self._find_api(api_data, f"documents/{ticker}")
        if not raw or not isinstance(raw, dict):
            return []

        docs = raw.get("documents", [])
        result = []
        for doc in docs[:10]:
            try:
                result.append(
                    AnalystDocument(
                        title=doc.get("title", ""),
                        author=doc.get("author"),
                        provider=doc.get("provider"),
                        updated_at=doc.get("updated_at"),
                    )
                )
            except Exception:
                continue

        logger.info(f"Extracted {len(result)} analyst documents for {ticker}")
        return result

    def _extract_financials(
        self, ticker: str, api_data: dict
    ) -> tuple[list[dict], list[dict]]:
        raw = self._find_api(api_data, f"financials/{ticker}")
        if not raw or not isinstance(raw, dict):
            return [], []

        annual = raw.get("annual", [])
        quarterly = raw.get("quarter", [])
        logger.info(f"Extracted financials for {ticker}")
        return annual, quarterly

from loguru import logger
from models.schema import (
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
            snapshot.earnings = self._extract_earnings(ticker, raw_api_data)
            annual, quarterly = self._extract_financials(ticker, raw_api_data)
            snapshot.financials_annual = annual
            snapshot.financials_quarterly = quarterly
        else:
            logger.debug(f"Live mode: skipped parsing financials for {ticker}")

        return snapshot

    def _find_api(self, api_data: dict, keyword: str) -> dict | list | None:
        """Find an API response by keyword in the key name."""
        for key, value in api_data.items():
            if keyword in key:
                return value
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

        # US stocks use "documents", Indian stocks use "sourced_reports"
        docs = raw.get("documents", [])
        reports = raw.get("sourced_reports", [])
        
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
                
        for rep in reports[:10]:
            try:
                result.append(
                    AnalystDocument(
                        title=rep.get("title", ""),
                        provider=rep.get("provider"),
                        updated_at=rep.get("date"),
                        outlook=rep.get("outlook"),
                        summary=rep.get("summary")
                    )
                )
            except Exception:
                continue

        logger.info(f"Extracted {len(result)} analyst documents/reports for {ticker}")
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

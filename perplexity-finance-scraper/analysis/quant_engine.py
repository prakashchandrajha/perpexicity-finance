from models.schema import TickerSnapshot
from models.yaml_schema import QuantMetrics

class QuantEngine:
    def __init__(self, snapshot: TickerSnapshot):
        self.snapshot = snapshot

    def analyze(self) -> QuantMetrics:
        """
        Compresses heavy historical arrays into token-efficient mathematical insights.
        """
        rev_growth = self._calc_revenue_growth()
        margin = self._calc_profit_margin()
        surprise = self._calc_earnings_surprise()
        momentum = self._calc_momentum()
        grade = self._grade_fundamentals(rev_growth, margin)

        return QuantMetrics(
            revenue_growth_yoy=f"{rev_growth:+.1f}%" if rev_growth is not None else "N/A",
            profit_margin_current=f"{margin:+.1f}%" if margin is not None else "N/A",
            earnings_surprise_avg=f"{surprise:+.1f}%" if surprise is not None else "N/A",
            momentum_52_week=momentum,
            fundamental_grade=grade
        )

    def _calc_revenue_growth(self) -> float | None:
        """Calculates YoY Revenue Growth from the latest two annual income statements."""
        try:
            # Look for income statements
            income_statements = [
                f for f in self.snapshot.financials_annual 
                if f.get("type") == "INCOME_STATEMENT"
            ]
            if not income_statements:
                return None
            
            data = income_statements[0].get("data", [])
            if len(data) >= 2:
                # Assuming data is chronologically ordered oldest to newest, but let's sort to be safe
                # Usually Perplexity returns oldest first (e.g. 2021, 2022, 2023, 2024)
                sorted_data = sorted(data, key=lambda x: x.get("fiscalYear", 0))
                latest_rev = sorted_data[-1].get("revenue")
                prev_rev = sorted_data[-2].get("revenue")
                
                if latest_rev and prev_rev and prev_rev != 0:
                    return ((latest_rev - prev_rev) / abs(prev_rev)) * 100
        except Exception:
            pass
        return None

    def _calc_profit_margin(self) -> float | None:
        """Calculates Net Income Margin from the latest annual income statement."""
        try:
            income_statements = [
                f for f in self.snapshot.financials_annual 
                if f.get("type") == "INCOME_STATEMENT"
            ]
            if not income_statements:
                return None
            
            data = income_statements[0].get("data", [])
            if len(data) >= 1:
                sorted_data = sorted(data, key=lambda x: x.get("fiscalYear", 0))
                latest = sorted_data[-1]
                net_income = latest.get("netIncome")
                revenue = latest.get("revenue")
                
                if net_income and revenue and revenue != 0:
                    return (net_income / revenue) * 100
        except Exception:
            pass
        return None

    def _calc_earnings_surprise(self) -> float | None:
        """Calculates the average EPS surprise across the last 4 reported quarters."""
        surprises = []
        for e in self.snapshot.earnings:
            if e.eps is not None and e.eps_estimated is not None and e.eps_estimated != 0:
                surprises.append((e.eps - e.eps_estimated) / abs(e.eps_estimated) * 100)
        
        if len(surprises) > 0:
            return sum(surprises[:4]) / len(surprises[:4])
        return None

    def _calc_momentum(self) -> str:
        """Calculates price proximity to 52-week highs/lows."""
        q = self.snapshot.quote
        if not q or not q.price or not q.year_high or not q.year_low:
            return "Unknown"
        
        dist_to_high = ((q.year_high - q.price) / q.year_high) * 100
        dist_to_low = ((q.price - q.year_low) / q.year_low) * 100
        
        if dist_to_high < 5:
            return f"Near 52W High ({dist_to_high:.1f}% away)"
        elif dist_to_low < 5:
            return f"Near 52W Low ({dist_to_low:.1f}% away)"
        else:
            return f"Mid-Range (+{dist_to_low:.1f}% from Low, -{dist_to_high:.1f}% from High)"

    def _grade_fundamentals(self, growth: float | None, margin: float | None) -> str:
        """Assigns a simple A-F grade based on growth and margins to bias the intraday bot."""
        if growth is None or margin is None:
            return "N/A"
        
        score = 0
        if growth > 15: score += 2
        elif growth > 5: score += 1
        elif growth < 0: score -= 2
        
        if margin > 20: score += 2
        elif margin > 10: score += 1
        elif margin < 0: score -= 2
        
        if score >= 3: return "A (Strong Buy Bias)"
        elif score == 2: return "B (Buy Bias)"
        elif score >= 0: return "C (Neutral)"
        elif score >= -2: return "D (Sell Bias)"
        else: return "F (Strong Sell Bias)"

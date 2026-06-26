import json
import logging

logger = logging.getLogger(__name__)

class DecisionEngine:
    """
    Fuses Quantitative data (from broker) and Qualitative data (from Perplexity)
    to generate a concrete trading signal.
    """
    
    def __init__(self):
        logger.info("[DecisionEngine] Initialized")
        
    def generate_signal(self, ticker: str, live_quote: dict, perplexity_data: dict) -> dict:
        """
        In a production environment, this builds a mega-prompt and queries Claude/Gemini.
        For now, we implement a rule-based/mock LLM output based on the Perplexity data.
        """
        logger.info(f"[DecisionEngine] Analyzing data for {ticker}...")
        
        # Extract features
        last_price = live_quote.get("last_price", 0)
        
        # Analyze Perplexity Data (Mock LLM reasoning)
        bullish_score = 0
        bearish_score = 0
        
        # Analyze Daily Analysis (most recent)
        recent_analysis = perplexity_data.get("daily_analysis", [])
        if recent_analysis:
            latest = recent_analysis[0].get("analysis", "").lower()
            if "upgraded" in latest or "gains" in latest or "higher" in latest or "upside" in latest:
                bullish_score += 2
            if "declining" in latest or "lower" in latest or "pressure" in latest or "outflows" in latest:
                bearish_score += 2
                
        # Analyze News
        for news in perplexity_data.get("news_headlines", []):
            hl = news.get("headline", "").lower()
            if "jump" in hl or "ipo" in hl or "strongest" in hl:
                bullish_score += 1
            if "loss" in hl or "strike" in hl or "fall" in hl:
                bearish_score += 1
                
        logger.info(f"[DecisionEngine] Sentiment Score -> Bullish: {bullish_score}, Bearish: {bearish_score}")
        
        # Decide
        if bullish_score > bearish_score:
            side = "BUY"
            target = round(last_price * 1.02, 2) # 2% target
            stop_loss = round(last_price * 0.99, 2) # 1% SL
            reason = "AI sentiment analysis of Perplexity narrative indicates strong bullish momentum."
        elif bearish_score > bullish_score:
            side = "SELL"
            target = round(last_price * 0.98, 2)
            stop_loss = round(last_price * 1.01, 2)
            reason = "AI sentiment analysis indicates bearish pressure from recent news/analysis."
        else:
            side = "HOLD"
            target = 0.0
            stop_loss = 0.0
            reason = "Conflicting or neutral signals."
            
        signal = {
            "ticker": ticker,
            "side": side,
            "current_price": last_price,
            "target": target,
            "stop_loss": stop_loss,
            "reason": reason,
            "confidence": 0.85
        }
        
        logger.info(f"[DecisionEngine] Generated Signal: {json.dumps(signal)}")
        return signal

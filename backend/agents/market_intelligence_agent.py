"""
SEED AI — Market Intelligence Agent (Production)
Fetches live market prices from Data.gov.in, uses Gemini for analysis.
Returns structured AgentResult — never fakes success.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent
from services.market_service import MarketService


class MarketAnalysis(BaseModel):
    crop: str
    current_price_per_kg: float
    price_trend: str
    sell_recommendation: str
    optimal_timing: str
    reasoning: str


class MarketIntelligenceAgent(BaseAgent):

    def __init__(self):
        super().__init__("MarketIntelligence")
        self.market_service = MarketService()

    def _process(self, context: Dict[str, Any]) -> tuple:
        crop = context.get("crop", "Tomato")
        location = context.get("location", "")
        self.log_execution(f"Fetching market data for {crop}")

        # Step 1: Get live market data
        raw_market = self.market_service.get_price(crop)
        tool_calls = ["Agmarknet/Data.gov.in API"]

        if "error" in raw_market:
            self.log_execution("Market API failed, using Gemini general knowledge")
            raw_market = {"source": "gemini_fallback", "crop": crop}
            tool_calls.append("Gemini Fallback")

        # Step 2: Use Gemini to analyze market
        prompt = f"""
You are an agricultural market analyst for Indian farmers.

Crop: {crop}
Location: {location}
Market data: {raw_market}

Analyze the market conditions and provide:
- Current estimated price per kg in INR
- Price trend (Rising / Falling / Stable)
- Whether to sell now, hold, or wait
- Optimal timing for selling
- Your reasoning

If live data is unavailable, use your knowledge of typical Indian market prices for this crop.
"""
        response = self.call_llm(prompt, schema=MarketAnalysis)
        result = MarketAnalysis.model_validate_json(response.text)
        tokens = response.total_tokens

        has_live_data = raw_market.get("source") != "gemini_fallback"
        return (
            result.model_dump(),
            tool_calls,
            tokens,
            80.0 if has_live_data else 45.0,
            result.reasoning,
        )

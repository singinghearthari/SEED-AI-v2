"""
SEED AI — Crop Prediction Agent (Production)
Predicts optimal crops based on location, season, soil, and budget.
Returns structured AgentResult — never fakes success.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent
from utils.dataset_manager import DatasetManager


class CropRecommendation(BaseModel):
    crop_name: str
    expected_yield_per_acre: str
    season_suitability: str
    market_demand: str
    investment_to_return_ratio: str


class CropPredictionResult(BaseModel):
    top_recommendations: list[CropRecommendation]
    seasonal_analysis: str
    soil_suitability_notes: str
    market_demand_forecast: str
    risk_factors: list[str]
    reasoning: str


class CropPredictionAgent(BaseAgent):

    def __init__(self):
        super().__init__("CropPrediction")
        self.dataset_manager = DatasetManager()

    def _process(self, context: Dict[str, Any]) -> tuple:
        location = context.get("location", "")
        crop = context.get("crop", "")
        budget = context.get("budget", 0)
        query = context.get("text_query", "")
        self.log_execution(f"Predicting optimal crops for location={location}, budget={budget}")

        # Retrieve knowledge base data
        crop_data = self.dataset_manager.query("crops", crop or location)
        soil_data = self.dataset_manager.query("soil_types", location)
        tool_calls = ["Knowledge Base (crops)", "Knowledge Base (soil_types)"]

        prompt = f"""
You are an expert agricultural advisor specializing in crop selection and yield prediction for Indian farmers.

Farmer's Query: {query}
Location: {location}
Current/Preferred Crop: {crop}
Available Budget: ₹{budget}
Crop Knowledge Base Data: {crop_data[:3] if crop_data else "No specific data available"}
Soil Knowledge Base Data: {soil_data[:3] if soil_data else "No specific data available"}

Based on this information, provide:
1. Top 3 recommended crops with:
   - Expected yield per acre (in kg or quintals)
   - Season suitability (Kharif/Rabi/Zaid)
   - Current market demand (High/Medium/Low)
   - Investment-to-return ratio (e.g., 1:2.5)
2. Seasonal analysis for the location
3. Soil suitability notes
4. Market demand forecast for the region
5. Risk factors to consider

Prioritize crops that maximize return within the given budget. Consider local climate, water availability, and market access.
"""
        response = self.call_llm(prompt, schema=CropPredictionResult)
        result = CropPredictionResult.model_validate_json(response.text)
        tokens = response.total_tokens

        has_kb_data = bool(crop_data or soil_data)
        return (
            result.model_dump(),
            tool_calls,
            tokens,
            80.0 if has_kb_data else 65.0,
            result.reasoning,
        )

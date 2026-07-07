"""
SEED AI — Soil & Nutrient Analyst Agent
Analyzes soil profile, NPK levels, pH, organic matter, and provides target fertilizer/amendment guidance.
Returns structured AgentResult.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent
from utils.dataset_manager import DatasetManager


class SoilNutrientResult(BaseModel):
    soil_ph: float
    nitrogen_level: str
    phosphorus_level: str
    potassium_level: str
    organic_carbon_percent: float
    nutrient_deficiencies: list[str]
    fertilizer_recommendations: list[str]
    soil_health_score: float
    soil_type_match: str
    reasoning: str


class SoilNutrientAgent(BaseAgent):

    def __init__(self):
        super().__init__("SoilNutrient")
        self.dataset_manager = DatasetManager()

    def _process(self, context: Dict[str, Any]) -> tuple:
        location = context.get("location", "")
        crop = context.get("crop", "")
        query = context.get("text_query", "")
        
        # User system context or inputs
        soil_type = context.get("soil_type", "Not Specified")

        self.log_execution(f"Analyzing soil nutrient profile for crop={crop}, location={location}, soil_type={soil_type}")

        # Retrieve knowledge base data
        soil_data = self.dataset_manager.query("soil_types", location or soil_type)
        tool_calls = ["Knowledge Base (soil_types)"]

        prompt = f"""
        You are an expert Soil Science & Nutrient Management Specialist.
        
        Farmer's Query: {query}
        Location: {location}
        Crop: {crop}
        Reported Soil Type: {soil_type}
        Soil Database Info: {soil_data[:3] if soil_data else "No specific data available"}
        
        Analyze the soil conditions:
        1. Est. Soil pH (5.0 to 8.5) and NPK level statuses (Adequate/Deficient/Critical).
        2. Est. Organic Carbon %.
        3. Highlight key nutrient deficiencies.
        4. Provide targeted organic/chemical fertilizer and micro-nutrient recommendations.
        5. Provide a soil health score out of 100.
        6. Confirm if soil type is suitable for {crop}.
        """
        response = self.call_llm(prompt, schema=SoilNutrientResult)
        result = SoilNutrientResult.model_validate_json(response.text)
        tokens = response.total_tokens

        has_kb_data = bool(soil_data)
        return (
            result.model_dump(),
            tool_calls,
            tokens,
            85.0 if has_kb_data else 65.0,
            result.reasoning,
        )

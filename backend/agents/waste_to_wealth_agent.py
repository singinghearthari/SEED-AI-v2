"""
SEED AI — Waste to Wealth Agent (Production)
Identifies revenue opportunities from agricultural waste streams.
Uses Hugging Face SigLIP2 for image-based waste classification when an image is provided.
Returns structured AgentResult — never fakes success.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent
from utils.dataset_manager import DatasetManager
from services.hf_vision_analyzer import HFVisionAnalyzer


class WasteOpportunity(BaseModel):
    waste_type: str
    conversion_method: str
    output_product: str
    estimated_revenue_per_ton: str
    required_investment: str
    difficulty_level: str


class WasteToWealthResult(BaseModel):
    waste_streams: list[str]
    opportunities: list[WasteOpportunity]
    total_potential_revenue: str
    equipment_needed: list[str]
    government_subsidies: list[str]
    environmental_benefits: list[str]
    quick_wins: list[str]
    reasoning: str


class WasteToWealthAgent(BaseAgent):

    def __init__(self):
        super().__init__("WasteToWealth")
        self.dataset_manager = DatasetManager()
        self.hf = HFVisionAnalyzer.get_instance()

    def _process(self, context: Dict[str, Any]) -> tuple:
        location = context.get("location", "")
        crop = context.get("crop", "")
        budget = context.get("budget", 0)
        query = context.get("text_query", "")
        self.log_execution(f"Analyzing waste-to-wealth for crop={crop}, location={location}")

        waste_classification = None
        image_bytes = context.get("image_bytes")
        image_base64 = context.get("image_base64")
        raw_bytes = image_bytes or (__import__("base64").b64decode(image_base64) if image_base64 else None)
        if raw_bytes and self.hf.is_available():
            waste_classification = self.hf.classify_waste(raw_bytes)
            self.log_execution(f"Waste image classification: {waste_classification.get('status')}")

        tool_calls = ["Knowledge Base (crops)", "Knowledge Base (government_schemes)"]
        if waste_classification and waste_classification["status"] == "success":
            tool_calls.append("HF Waste Classifier (SigLIP2)")

        crop_data = self.dataset_manager.query("crops", crop)
        scheme_data = self.dataset_manager.query("government_schemes", "waste")

        waste_context = ""
        if waste_classification and waste_classification["status"] == "success":
            top_waste = waste_classification["predictions"][:3]
            waste_context = "Waste material detected in image:\n" + "\n".join(
                f"  - {p['label']} (confidence: {p['score']*100:.1f}%)"
                for p in top_waste
            )

        prompt = f"""
You are an expert in agricultural waste management and circular economy, specializing in Indian farming.

Farmer's Query: {query}
Location: {location}
Crop: {crop}
Available Budget for Investment: ₹{budget}
{waste_context}
Crop Knowledge Base Data: {crop_data[:3] if crop_data else "No specific data available"}
Government Schemes Data: {scheme_data[:3] if scheme_data else "No specific data available"}

Analyze the agricultural waste streams from this crop and identify wealth-generation opportunities:

1. Available waste streams from {crop} (e.g., stalks, husks, leaves, roots, etc.)
2. For each viable opportunity, provide:
   - Waste type being converted
   - Conversion method (composting, biochar, briquettes, mushroom cultivation, animal feed, vermicompost, biofuel, paper/packaging, etc.)
   - Output product
   - Estimated revenue per ton of waste processed (in ₹)
   - Required investment to start (in ₹)
   - Difficulty level (Easy/Medium/Hard)
3. Total potential annual revenue from waste conversion
4. Equipment needed (list specific items)
5. Available government subsidies and schemes for waste processing
6. Environmental benefits (carbon credits, soil health, water conservation)
7. Quick wins — things the farmer can start doing THIS WEEK with minimal investment

Focus on practical, actionable opportunities. Prioritize low-investment, high-return options suitable for small/medium Indian farmers.
"""
        response = self.call_llm(prompt, schema=WasteToWealthResult)
        result = WasteToWealthResult.model_validate_json(response.text)
        tokens = response.total_tokens

        has_kb_data = bool(crop_data or scheme_data)
        return (
            result.model_dump(),
            tool_calls,
            tokens,
            78.0 if has_kb_data else 62.0,
            result.reasoning,
        )

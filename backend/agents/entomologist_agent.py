"""
SEED AI — Entomologist Agent (Pest Specialist)
Specializes in identifying crop pests, insects, and recommending target pesticides, biological controls, and thresholds.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent
from utils.dataset_manager import DatasetManager


class PestAnalysisResult(BaseModel):
    pest_name: str
    risk_level: str  # Critical / High / Medium / Low
    symptoms: list[str]
    economic_threshold_info: str
    chemical_controls: list[str]
    biological_controls: list[str]
    preventive_cultural_practices: list[str]
    reasoning: str


class EntomologistAgent(BaseAgent):

    def __init__(self):
        super().__init__("Entomologist")
        self.dataset_manager = DatasetManager()

    def _process(self, context: Dict[str, Any]) -> tuple:
        crop = context.get("crop", "")
        query = context.get("text_query", "")

        self.log_execution(f"Analyzing insect/pest status for crop={crop}")

        # Retrieve knowledge base data
        pests_data = self.dataset_manager.query("diseases", crop)  # diseases dataset often contains pests in agricultural contexts
        tool_calls = ["Knowledge Base (pests)"]

        prompt = f"""
        You are an expert Entomologist and Integrated Pest Management (IPM) Specialist.
        
        Farmer's Query: {query}
        Crop: {crop}
        Pest/Disease Database Info: {pests_data[:3] if pests_data else "No specific database entry"}
        
        Provide:
        1. Identify potential pests/insects causing the reported issue or relevant to the crop.
        2. Assign a risk level (Critical/High/Medium/Low).
        3. List standard symptoms of infestation.
        4. Define the Economic Injury Level / Economic Threshold (ETL) for spraying.
        5. Detail specific chemical controls (chemical names, dosages).
        6. Detail biological controls (beneficial insects, botanical sprays like neem oil).
        7. Cultural practices to prevent infestation.
        """
        response = self.call_llm(prompt, schema=PestAnalysisResult)
        result = PestAnalysisResult.model_validate_json(response.text)
        tokens = response.total_tokens

        return (
            result.model_dump(),
            tool_calls,
            tokens,
            80.0 if pests_data else 65.0,
            result.reasoning,
        )

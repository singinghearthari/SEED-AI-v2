"""
SEED AI — Government Scheme Agent (Production)
Retrieves government scheme data from knowledge base.
Returns structured AgentResult — never fakes success.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent
from utils.dataset_manager import DatasetManager


class SchemeDetail(BaseModel):
    name: str
    type: str
    benefits: str
    eligibility: str


class GovernmentSchemeResult(BaseModel):
    eligible_schemes: list[str]
    scheme_details: list[SchemeDetail]
    application_guidance: str
    reasoning: str


class GovernmentSchemeAgent(BaseAgent):

    def __init__(self):
        super().__init__("GovernmentScheme")
        self.dataset_manager = DatasetManager()

    def _process(self, context: Dict[str, Any]) -> tuple:
        crop = context.get("crop", "")
        budget = context.get("budget", 0)
        location = context.get("location", "")
        self.log_execution(f"Finding government schemes for crop={crop}, location={location}")

        # Step 1: Retrieve schemes from knowledge base
        scheme_data = self.dataset_manager.query("government_schemes", crop or "farmer")
        tool_calls = ["Knowledge Base (government_schemes)"]

        prompt = f"""
You are an Indian agricultural policy advisor.

Farmer details:
- Crop: {crop}
- Budget: ₹{budget}
- Location: {location}

Available government schemes from database: {scheme_data}

Based on this, identify:
1. Which schemes this farmer is eligible for (list of names)
2. Details for each scheme (name, type, benefits, eligibility)
3. Step-by-step guidance on how to apply
4. Your reasoning on prioritization

If no schemes are found in the database, use your knowledge of current Indian agricultural schemes.
"""
        response = self.call_llm(prompt, schema=GovernmentSchemeResult)
        result = GovernmentSchemeResult.model_validate_json(response.text)
        tokens = response.total_tokens

        return (
            result.model_dump(),
            tool_calls,
            tokens,
            75.0 if scheme_data else 50.0,
            result.reasoning,
        )

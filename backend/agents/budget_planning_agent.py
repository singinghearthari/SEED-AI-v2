"""
SEED AI — Budget Planning Agent (Production)
Retrieves treatment costs from knowledge base, uses Gemini to recommend plans.
Returns structured AgentResult — never fakes success.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent
from utils.dataset_manager import DatasetManager


class TreatmentOption(BaseModel):
    name: str
    type: str
    application: str
    cost_estimate_inr: float
    effectiveness: str


class BudgetPlan(BaseModel):
    cheapest_option: TreatmentOption
    best_value_option: TreatmentOption
    budget_limit: float
    estimated_total_cost: float
    budget_compliant: bool
    savings_tip: str
    reasoning: str


class BudgetPlanningAgent(BaseAgent):

    def __init__(self):
        super().__init__("BudgetPlanning")
        self.dataset_manager = DatasetManager()

    def _process(self, context: Dict[str, Any]) -> tuple:
        budget = context.get("budget", 0)
        disease = context.get("disease", "")
        crop = context.get("crop", "")
        self.log_execution(f"Planning budget for limit ₹{budget}")

        # Step 1: Retrieve treatment data from knowledge base
        treatments_data = self.dataset_manager.query("treatments", disease or crop)
        tool_calls = ["Knowledge Base (treatments)"]

        prompt = f"""
You are a farm budget planning advisor for Indian farmers.

Budget limit: ₹{budget}
Crop: {crop}
Disease detected: {disease}
Available treatment data from knowledge base: {treatments_data}

Based on this information, recommend:
1. The cheapest treatment option (name, type, application method, cost in INR, effectiveness)
2. The best value option (best effectiveness-to-cost ratio)
3. Whether the total cost fits within the budget
4. A practical savings tip

If no treatment data is available, use your agricultural knowledge.
All costs must be in Indian Rupees (INR).
"""
        response = self.call_llm(prompt, schema=BudgetPlan)
        result = BudgetPlan.model_validate_json(response.text)
        tokens = response.total_tokens

        return (
            result.model_dump(),
            tool_calls,
            tokens,
            80.0 if treatments_data else 55.0,
            result.reasoning,
        )

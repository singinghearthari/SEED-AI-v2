"""
SEED AI — Task Planning Agent (Production)
Generates a 7-day farming schedule from all collected context.
Returns structured AgentResult — never fakes success.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent


class FarmTask(BaseModel):
    day: str
    task: str
    reason: str
    expected_outcome: str
    priority: str


class TaskPlanResult(BaseModel):
    daily_tasks: list[FarmTask]
    timeline_summary: str
    follow_up_date: str
    reasoning: str


class TaskPlanningAgent(BaseAgent):

    def __init__(self):
        super().__init__("TaskPlanning")

    def _process(self, context: Dict[str, Any]) -> tuple:
        self.log_execution("Generating farming schedule from agent context")

        # Build a sanitized context (no image bytes)
        safe_context = {
            k: v for k, v in context.items()
            if k not in ("image_bytes", "image_base64")
        }

        prompt = f"""
You are a farm task scheduler for Indian farmers.

Context from all agents:
{safe_context}

Based on this complete context, generate a practical 7-day farming schedule.

For each task include:
- Day (Today, Tomorrow, Day 3, etc.)
- Specific task to perform
- Reason for this task
- Expected outcome
- Priority (Critical / High / Medium / Low)

Also provide a timeline summary and recommended follow-up date.
Consider weather conditions, disease urgency, budget limits, and market timing.
"""
        response = self.call_llm(prompt, schema=TaskPlanResult)
        result = TaskPlanResult.model_validate_json(response.text)
        tokens = response.total_tokens

        return (
            result.model_dump(),
            ["Gemini Scheduler"],
            tokens,
            70.0,
            result.reasoning,
        )

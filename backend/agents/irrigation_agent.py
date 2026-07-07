"""
SEED AI — Irrigation Specialist Agent
Specializes in water scheduling, irrigation system types, soil moisture management, and water budgeting.
"""
from typing import Dict, Any
from pydantic import BaseModel
from .base_agent import BaseAgent
from utils.dataset_manager import DatasetManager


class IrrigationResult(BaseModel):
    irrigation_schedule_7day: list[str]
    recommended_irrigation_method: str  # Drip, Sprinkler, Flood, Furrow
    water_requirement_liters_per_acre_daily: float
    moisture_conservation_tips: list[str]
    system_maintenance_protocols: list[str]
    reasoning: str


class IrrigationAgent(BaseAgent):

    def __init__(self):
        super().__init__("Irrigation")
        self.dataset_manager = DatasetManager()

    def _process(self, context: Dict[str, Any]) -> tuple:
        crop = context.get("crop", "")
        location = context.get("location", "")
        query = context.get("text_query", "")

        # Incorporate weather context if available
        weather_summary = ""
        agent_results = context.get("agent_results", {})
        if "weather" in agent_results:
            weather_data = agent_results["weather"]
            if isinstance(weather_data, dict) and weather_data.get("data"):
                weather_summary = str(weather_data["data"])

        self.log_execution(f"Calculating irrigation parameters for crop={crop}, location={location}")

        # Retrieve knowledge base data
        crop_data = self.dataset_manager.query("crops", crop)
        tool_calls = ["Knowledge Base (crops)", "Weather Context"]

        prompt = f"""
        You are an expert Agricultural Irrigation Engineer and Hydrology Specialist.
        
        Farmer's Query: {query}
        Crop: {crop}
        Location: {location}
        Weather Forecast/Context: {weather_summary if weather_summary else "Not available — assume local seasonal averages"}
        Crop database info: {crop_data[:2] if crop_data else "No specific data"}
        
        Analyze the water requirements:
        1. Formulate a 7-day irrigation schedule (days to water, duration, volume).
        2. Recommend the best irrigation method (e.g. drip, sprinkler, furrow) for this crop/location.
        3. Estimate average daily water requirements in Liters/Acre.
        4. List moisture conservation tips (mulching, organic matter).
        5. Detail irrigation system maintenance protocols (filter flushing, emitter cleaning).
        """
        response = self.call_llm(prompt, schema=IrrigationResult)
        result = IrrigationResult.model_validate_json(response.text)
        tokens = response.total_tokens

        return (
            result.model_dump(),
            tool_calls,
            tokens,
            85.0 if crop_data else 70.0,
            result.reasoning,
        )

"""
SEED AI — Core Data Models (Production v2)
Production-grade Pydantic models for structured agent communication.
Every agent returns an AgentResult. The orchestrator assembles a PipelineResult.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class AgentStatus(str, Enum):
    """Truthful status codes — never fake success."""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"
    CONFIGURATION_ERROR = "configuration_error"
    RETRYING = "retrying"
    RUNNING = "running"


class AgentResult(BaseModel):
    """
    Standardized result envelope returned by every agent.
    The orchestrator and frontend consume this shape exclusively.
    """
    status: AgentStatus
    agent_name: str
    execution_time_ms: float = 0.0
    tool_calls: List[str] = Field(default_factory=list)
    tokens_used: int = 0
    confidence: float = 0.0
    reasoning: str = ""
    error: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    retries: int = 0
    model: str = ""
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def succeeded(self) -> bool:
        return self.status == AgentStatus.SUCCESS


class FusionResult(BaseModel):
    """
    Output of the Decision Fusion engine.
    confidence_score is computed (0-100), never free-text.
    """
    summary: str
    recommended_actions: list[str] = Field(default_factory=list)
    confidence_score: int = 0
    confidence_label: str = ""
    risk_level: str = "Unknown"
    budget_assessment: str = ""
    weather_consideration: str = ""
    evidence_sources: list[str] = Field(default_factory=list)
    agents_used: list[str] = Field(default_factory=list)
    tools_executed: list[str] = Field(default_factory=list)
    alternatives_considered: list[str] = Field(default_factory=list)
    government_schemes: list[str] = Field(default_factory=list)
    follow_up_actions: list[str] = Field(default_factory=list)
    is_degraded: bool = False
    failed_agents: list[str] = Field(default_factory=list)
    degradation_reasons: list[str] = Field(default_factory=list)

    @staticmethod
    def confidence_to_label(score: int) -> str:
        if score >= 70:
            return "High"
        elif score >= 40:
            return "Medium"
        return "Low"

    def compute_label(self):
        self.confidence_label = self.confidence_to_label(self.confidence_score)


class LLMFusionSchema(BaseModel):
    """Schema sent to Gemini for structured fusion output (LLM-side)."""
    summary: str
    recommended_actions: list[str]
    confidence: str
    risk_level: str
    budget_assessment: str
    weather_consideration: str
    evidence_sources: list[str]
    agents_used: list[str]
    tools_executed: list[str]
    alternatives_considered: list[str]
    government_schemes: list[str]
    follow_up_actions: list[str]


class ProgressEvent(BaseModel):
    """Structured progress event for SSE streaming."""
    type: str = "progress"
    phase: str
    progress: int = 0
    total: int = 100
    message: str = ""
    status: str = "running"
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class ExecutionReport(BaseModel):
    """
    Comprehensive execution report for download/export.
    Contains all data needed for post-simulation analysis.
    """
    report_title: str = "SEED AI Simulation Report"
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    request_id: str = ""
    trace_id: str = ""
    query: str = ""
    location: str = ""
    crop: str = ""
    budget: float = 0.0
    execution_mode: str = "auto"
    total_latency_ms: float = 0.0
    total_tokens: int = 0
    agents_executed: list[str] = Field(default_factory=list)
    agents_succeeded: list[str] = Field(default_factory=list)
    agents_failed: list[str] = Field(default_factory=list)
    fusion_result: Optional[Dict[str, Any]] = None
    agent_results: Dict[str, Any] = Field(default_factory=dict)
    agent_metadata: Dict[str, Any] = Field(default_factory=dict)
    performance_metrics: Dict[str, Any] = Field(default_factory=dict)
    execution_log: list[Dict[str, Any]] = Field(default_factory=list)
    is_degraded: bool = False
    status: str = "completed"

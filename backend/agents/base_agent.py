"""
SEED AI — Production Base Agent (v3 — Async Optimized)
All agents inherit from this. Provides:
- Shared Gemini client (singleton via gemini_service)
- Structured AgentResult returns
- Sync + async execute() wrappers with timing, error handling, retry tracking
- Input sanitization
"""
import asyncio
import re
import time
import logging
from typing import Any, Dict, Optional

from models.schemas import AgentResult, AgentStatus
from services import gemini_service


class BaseAgent:
    """
    Production Base Agent for SEED AI.
    Every sub-agent must implement _process(context) -> tuple (sync) or
    _process_async(context) -> tuple (async, preferred for performance).
    Call execute(context) or async_execute(context) for structured AgentResult.
    """

    def __init__(self, name: str):
        self.name = name
        self.logger = logging.getLogger(f"Agent.{name}")
        self.default_model = gemini_service.DEFAULT_MODEL
        self.total_tokens_used = 0

    def execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Sync execution with full timing, error handling, and structured output.
        Uses to_thread internally if agent implements _process_async.
        """
        start = time.time()

        if not gemini_service.is_available():
            elapsed = (time.time() - start) * 1000
            error_msg = gemini_service.get_init_error() or "Gemini client unavailable"
            self.logger.error(f"[{self.name}] Configuration error: {error_msg}")
            return AgentResult(
                status=AgentStatus.CONFIGURATION_ERROR,
                agent_name=self.name,
                execution_time_ms=round(elapsed, 1),
                error=error_msg,
                model=self.default_model,
            )

        try:
            self.log_execution("Starting")
            data, tool_calls, tokens, confidence, reasoning = self._process(context)
            elapsed = (time.time() - start) * 1000
            self.total_tokens_used += tokens
            self.log_execution(f"Completed in {elapsed:.0f}ms")

            return AgentResult(
                status=AgentStatus.SUCCESS,
                agent_name=self.name,
                execution_time_ms=round(elapsed, 1),
                tool_calls=tool_calls,
                tokens_used=tokens,
                confidence=confidence,
                reasoning=reasoning,
                data=data,
                model=self.default_model,
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            error_msg = str(e)
            self.logger.error(f"[{self.name}] Failed: {error_msg}")
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                execution_time_ms=round(elapsed, 1),
                error=error_msg,
                model=self.default_model,
            )

    async def async_execute(self, context: Dict[str, Any]) -> AgentResult:
        """
        Fully async execution path.
        Uses _process_async if available, otherwise falls back to _process via thread.
        Preferred over execute() for performance — avoids thread pool overhead.
        """
        start = time.time()

        if not gemini_service.is_available():
            elapsed = (time.time() - start) * 1000
            error_msg = gemini_service.get_init_error() or "Gemini client unavailable"
            self.logger.error(f"[{self.name}] Configuration error: {error_msg}")
            return AgentResult(
                status=AgentStatus.CONFIGURATION_ERROR,
                agent_name=self.name,
                execution_time_ms=round(elapsed, 1),
                error=error_msg,
                model=self.default_model,
            )

        try:
            self.log_execution("Starting (async)")
            if hasattr(self, '_process_async'):
                data, tool_calls, tokens, confidence, reasoning = await self._process_async(context)
            else:
                data, tool_calls, tokens, confidence, reasoning = await asyncio.to_thread(
                    self._process, context
                )
            elapsed = (time.time() - start) * 1000
            self.total_tokens_used += tokens
            self.log_execution(f"Completed in {elapsed:.0f}ms (async)")

            return AgentResult(
                status=AgentStatus.SUCCESS,
                agent_name=self.name,
                execution_time_ms=round(elapsed, 1),
                tool_calls=tool_calls,
                tokens_used=tokens,
                confidence=confidence,
                reasoning=reasoning,
                data=data,
                model=self.default_model,
            )
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            error_msg = str(e)
            self.logger.error(f"[{self.name}] Failed (async): {error_msg}")
            return AgentResult(
                status=AgentStatus.FAILED,
                agent_name=self.name,
                execution_time_ms=round(elapsed, 1),
                error=error_msg,
                model=self.default_model,
            )

    def _process(self, context: Dict[str, Any]) -> tuple:
        """
        Subclasses must implement this (sync version).
        Returns: (data_dict, tool_calls_list, tokens_int, confidence_float, reasoning_str)
        Should raise exceptions on failure (execute() catches them).
        """
        raise NotImplementedError("Subclasses must implement _process()")

    async def _process_async(self, context: Dict[str, Any]) -> tuple:
        """
        Optional async version of _process. If implemented, async_execute uses this
        directly instead of offloading _process to a thread pool.
        Returns: (data_dict, tool_calls_list, tokens_int, confidence_float, reasoning_str)
        """
        return await asyncio.to_thread(self._process, context)

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Legacy interface. Returns raw dict for backward compatibility
        with MemoryAgent and other non-LLM agents.
        """
        raise NotImplementedError("Subclasses must implement process()")

    def log_execution(self, status: str, details: Optional[str] = None):
        """Structured logging for observability."""
        msg = f"[{self.name}] {status}"
        if details:
            msg += f" — {details}"
        self.logger.info(msg)

    def call_llm(self, prompt: str, schema: Optional[Any] = None) -> gemini_service.GenerationResult:
        """
        Sync Gemini call via the centralized service.
        """
        return gemini_service.generate(
            prompt=prompt,
            schema=schema,
            model=self.default_model,
        )

    async def async_call_llm(self, prompt: str, schema: Optional[Any] = None) -> gemini_service.GenerationResult:
        """
        Async Gemini call — uses async_generate to avoid blocking the event loop.
        Preferred over call_llm() in async contexts.
        """
        return await gemini_service.async_generate(
            prompt=prompt,
            schema=schema,
            model=self.default_model,
        )

    @staticmethod
    def sanitize_input(text: str) -> str:
        """
        Sanitizes user input to mitigate prompt injection attacks.
        Strips common injection patterns while preserving valid agricultural content.
        """
        if not text:
            return ""
        injection_patterns = [
            r"ignore\s+(all\s+)?(previous|above|prior)\s+instructions",
            r"forget\s+(all\s+)?(previous|above|prior)\s+instructions",
            r"you\s+are\s+now\s+a",
            r"new\s+instructions?:",
            r"system\s*:\s*",
            r"<\s*/?\s*system\s*>",
        ]
        sanitized = text
        for pattern in injection_patterns:
            sanitized = re.sub(pattern, "[FILTERED]", sanitized, flags=re.IGNORECASE)
        return sanitized.strip()

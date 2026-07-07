"""
SEED AI — Centralized Gemini Service (Singleton v3)
Single shared client for all agents. Validates API keys at startup.
Provides health_check(), generate(), and generate_with_vision() with:
- Multi-key failover (GEMINI_API_KEY + GEMINI_API_KEY1..5)
- Rate limiting (15 RPM per key with safety margin)
- Auto key rotation on 429 / quota exhaustion
- Key cooldown: temporarily blacklists a key after 429
- Retry with exponential backoff + 429-aware wait
- Token tracking
- Async-aware rate limiting
"""
import os
import re
import time
import asyncio
import logging
import threading
from typing import Any, Optional, List
from google import genai
from google.genai import types
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
import json

logger = logging.getLogger("GeminiService")

_clients: List[Optional[genai.Client]] = []
_api_keys: List[str] = []
_current_key_index: int = 0
_initialized: bool = False
_init_error: Optional[str] = None

_key_cooldowns: dict[int, float] = {}
_key_cooldown_lock = threading.Lock()
KEY_COOLDOWN_SECONDS = 30

API_KEY_ENV_VARS = [
    "GEMINI_API_KEY",
    "GEMINI_API_KEY1",
    "GEMINI_API_KEY2",
    "GEMINI_API_KEY3",
    "GEMINI_API_KEY4",
    "GEMINI_API_KEY5",
    "GEMINI_API_KEY6",
    "GEMINI_API_KEY7",
    "GEMINI_API_KEY8",
    "GEMINI_API_KEY9",
    "GEMINI_API_KEY10",
]

DEFAULT_MODEL = "gemini-2.0-flash"

SAFETY_SETTINGS = [
    types.SafetySetting(
        category="HARM_CATEGORY_DANGEROUS_CONTENT",
        threshold="BLOCK_ONLY_HIGH",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_HARASSMENT",
        threshold="BLOCK_ONLY_HIGH",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_HATE_SPEECH",
        threshold="BLOCK_ONLY_HIGH",
    ),
    types.SafetySetting(
        category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
        threshold="BLOCK_ONLY_HIGH",
    ),
]


class AsyncRateLimiter:
    """
    Thread-safe rate limiter for Gemini API.
    Uses threading.Lock (cross-event-loop-safe) + asyncio.sleep for non-blocking waits.
    Never sleeps while holding the lock.
    """

    def __init__(self, max_per_minute: int = 4):
        self.max_per_minute = max_per_minute
        self.min_interval = 60.0 / max_per_minute if max_per_minute > 0 else 60.0
        self._timestamps: list[float] = []
        self._lock = threading.Lock()

    def _check_wait_time(self) -> float:
        """Non-blocking: returns seconds to wait, or 0 if ready to proceed."""
        with self._lock:
            now = time.time()
            self._timestamps = [t for t in self._timestamps if now - t < 60.0]
            if len(self._timestamps) >= self.max_per_minute:
                oldest = self._timestamps[0]
                return 60.0 - (now - oldest) + 1.0
            if self._timestamps:
                last = self._timestamps[-1]
                elapsed = now - last
                if elapsed < self.min_interval:
                    return self.min_interval - elapsed
            self._timestamps.append(time.time())
            return 0.0

    async def wait_if_needed(self):
        """Async wait — never blocks the event loop during sleep."""
        wait = self._check_wait_time()
        if wait > 0:
            logger.info(f"Rate limiter: waiting {wait:.1f}s (at {self.max_per_minute} RPM limit)")
            await asyncio.sleep(wait)
            with self._lock:
                self._timestamps.append(time.time())

    def sync_wait_if_needed(self):
        """Sync wait — safe to call from any thread (uses time.sleep)."""
        wait = self._check_wait_time()
        if wait > 0:
            logger.info(f"Rate limiter: waiting {wait:.1f}s (sync, at {self.max_per_minute} RPM limit)")
            time.sleep(wait)
            with self._lock:
                self._timestamps.append(time.time())


_rate_limiter = AsyncRateLimiter(max_per_minute=4)

# Global concurrency semaphore: limits parallel Gemini requests
# Matches available key count so all keys can be utilized simultaneously
_gemini_concurrency = threading.Semaphore(3)
_gemini_concurrency_max = 3


def _check_groq_available() -> bool:
    try:
        import groq  # noqa: F401
        return True
    except ImportError:
        return False


def _check_g4f_available() -> bool:
    try:
        import g4f  # noqa: F401
        return True
    except ImportError:
        return False


# Cache whether fallback libs are importable (checked once at startup)
_groq_available: bool = _check_groq_available()
_g4f_available: bool = _check_g4f_available()


def groq_available() -> bool:
    return _groq_available


def g4f_available() -> bool:
    return _g4f_available


def set_rate_limit(max_per_minute: int):
    global _rate_limiter
    _rate_limiter = AsyncRateLimiter(max_per_minute=max_per_minute)
    logger.info(f"Rate limit updated to {max_per_minute} RPM")


def set_concurrency(max_concurrent: int):
    global _gemini_concurrency, _gemini_concurrency_max
    _gemini_concurrency = threading.Semaphore(max_concurrent)
    _gemini_concurrency_max = max_concurrent
    logger.info(f"Gemini concurrency set to {max_concurrent}")


def _collect_api_keys() -> List[str]:
    keys = []
    for env_var in API_KEY_ENV_VARS:
        key = os.getenv(env_var, "")
        if key and not key.startswith("AIzaSyBk_placeholder"):
            if key not in keys:
                keys.append(key)
            else:
                logger.info(f"Skipping duplicate key from {env_var}")
    logger.info(f"Collected {len(keys)} unique API keys")
    return keys


def _is_key_on_cooldown(index: int) -> bool:
    with _key_cooldown_lock:
        expiry = _key_cooldowns.get(index)
        if expiry and time.time() < expiry:
            return True
        if expiry:
            del _key_cooldowns[index]
        return False


def _mark_key_cooldown(index: int):
    with _key_cooldown_lock:
        _key_cooldowns[index] = time.time() + KEY_COOLDOWN_SECONDS


def _get_available_client_indices() -> List[int]:
    return [
        i for i, c in enumerate(_clients)
        if c is not None and not _is_key_on_cooldown(i)
    ]


def _rotate_key():
    global _current_key_index
    available = _get_available_client_indices()
    if not available:
        # Don't clear cooldowns — prevents infinite retry loop on daily quota exhaustion.
        # The caller (generate functions) will fall through to g4f and then raise.
        return
    
    if _current_key_index in available:
        current_pos = available.index(_current_key_index)
        next_pos = (current_pos + 1) % len(available)
    else:
        next_pos = 0
    _current_key_index = available[next_pos]


def init_gemini() -> None:
    global _clients, _api_keys, _initialized, _init_error

    if _initialized:
        return

    _api_keys = _collect_api_keys()
    if not _api_keys:
        _init_error = (
            "No valid GEMINI_API_KEY environment variables found. "
            "Set GEMINI_API_KEY (or GEMINI_API_KEY1..GEMINI_API_KEY4 for failover)."
        )
        logger.error(_init_error)
        _initialized = True
        return

    _clients = []
    for idx, key in enumerate(_api_keys):
        try:
            client = genai.Client(api_key=key)
            _clients.append(client)
            logger.info(f"Gemini client {idx + 1}/{len(_api_keys)} initialized.")
        except Exception as e:
            logger.warning(f"Gemini client {idx + 1} initialization failed: {e}")
            _clients.append(None)

    healthy = sum(1 for c in _clients if c is not None)
    if healthy == 0:
        _init_error = "All Gemini clients failed to initialize."
    else:
        logger.info(f"{healthy}/{len(_clients)} Gemini clients ready.")
        _init_error = None
        total_rpm = healthy * 15
        set_rate_limit(total_rpm)
        set_concurrency(healthy)
        logger.info(f"Rate limit set to {total_rpm} RPM across {healthy} keys")

    _initialized = True


def get_client() -> Optional[genai.Client]:
    if not _initialized:
        init_gemini()
    if not _clients:
        return None
    
    # True connection pooling: Load balance by rotating key on EVERY request
    _rotate_key()
    
    # Skip keys on cooldown — rotate until we find one that's available
    for _ in range(len(_clients)):
        idx = _current_key_index
        if not _is_key_on_cooldown(idx):
            client = _clients[idx]
            if client is not None:
                return client
        _rotate_key()
    
    return None


def get_current_key_index() -> int:
    return _current_key_index


def is_available() -> bool:
    if not _initialized:
        init_gemini()
    return any(c is not None for c in _clients)


def get_init_error() -> Optional[str]:
    if not _initialized:
        init_gemini()
    return _init_error


def health_check() -> dict:
    if not _initialized:
        init_gemini()

    client = get_client()
    status: dict[str, Any] = {
        "available": client is not None,
        "model": DEFAULT_MODEL,
        "error": _init_error,
        "active_key_index": _current_key_index,
        "total_keys": len(_api_keys),
    }

    if client is not None:
        try:
            _rate_limiter.sync_wait_if_needed()
            start = time.time()
            response = client.models.generate_content(
                model=DEFAULT_MODEL,
                contents="Reply with exactly: OK",
                config=types.GenerateContentConfig(
                    temperature=0.0,
                    max_output_tokens=5,
                ),
            )
            latency_ms = (time.time() - start) * 1000
            status["ping"] = "ok"
            status["ping_latency_ms"] = round(latency_ms, 1)
        except Exception as e:
            status["ping"] = "failed"
            status["ping_error"] = str(e)
            _rotate_key()

    return status


class GenerationResult:
    """Wraps a Gemini response with extracted metadata."""

    def __init__(
        self,
        text: str,
        prompt_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: float = 0.0,
        model: str = DEFAULT_MODEL,
    ):
        self.text = text
        self.prompt_tokens = prompt_tokens
        self.output_tokens = output_tokens
        self.total_tokens = prompt_tokens + output_tokens
        self.latency_ms = latency_ms
        self.model = model


def _extract_retry_delay(error: Exception) -> Optional[float]:
    msg = str(error)
    match = re.search(r"retry in (\d+(?:\.\d+)?)", msg, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _handle_rate_limit_error(error: Exception) -> None:
    delay = _extract_retry_delay(error)
    if delay and delay > 0:
        wait = min(delay + 2.0, 90.0)
        logger.warning(f"429 Rate limited. Waiting {wait:.1f}s before retry...")
        time.sleep(wait)


GROQ_MODEL = "llama-3.1-70b-versatile"


def _groq_fallback(
    prompt: Any,
    schema: Optional[Any] = None,
    model: str = GROQ_MODEL,
) -> Optional[GenerationResult]:
    """Fallback generator using Groq when Gemini limits are reached.
    Returns None if Groq key is not set or call fails."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        logger.warning("GROQ_API_KEY not set — skipping Groq fallback")
        return None
    if not _groq_available:
        logger.warning("groq SDK not installed — skipping Groq fallback")
        return None
    logger.warning(f"Using Groq ({model}) fallback due to Gemini limits...")
    try:
        from groq import Groq
        client = Groq(api_key=groq_api_key)
        messages = []

        prompt_text = prompt
        if isinstance(prompt, list):
            prompt_text = next((item for item in prompt if isinstance(item, str)), "Please analyze the input.")

        if schema:
            if hasattr(schema, "model_json_schema"):
                schema_dict = schema.model_json_schema()
                schema_str = json.dumps(schema_dict, indent=2)
                sys_msg = (
                    "You must return ONLY a raw valid JSON object. "
                    "Do not use markdown code blocks like ```json. "
                    f"Your JSON must strictly match this schema:\n{schema_str}"
                )
                messages.append({"role": "system", "content": sys_msg})

        messages.append({"role": "user", "content": str(prompt_text)})

        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
        )
        result_text = response.choices[0].message.content or ""
        latency_ms = (time.time() - start) * 1000

        if schema:
            result_text = result_text.strip("` \n")
            if result_text.startswith("json\n"):
                result_text = result_text[5:]

        usage = response.usage
        prompt_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return GenerationResult(
            text=result_text,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            model=f"{model} (groq fallback)"
        )
    except Exception as e:
        logger.error(f"Groq fallback failed: {e}")
        return None


def _fallback_generate(
    prompt: Any,
    schema: Optional[Any] = None,
    model: str = "gpt-4o"
) -> Optional[GenerationResult]:
    """Fallback generator using unlimited free tier g4f api when Gemini limits are reached.
    Returns None if g4f is not installed or fails."""
    if not _g4f_available:
        logger.warning("g4f not installed — skipping fallback")
        return None
    logger.warning("Using g4f (gpt-4o) fallback due to Gemini limits...")
    try:
        from g4f.client import Client
        client = Client()
        messages = []

        prompt_text = prompt
        if isinstance(prompt, list):
            prompt_text = next((item for item in prompt if isinstance(item, str)), "Please analyze the input.")

        if schema:
            if hasattr(schema, "model_json_schema"):
                schema_dict = schema.model_json_schema()
                schema_str = json.dumps(schema_dict, indent=2)
                sys_msg = (
                    "You must return ONLY a raw valid JSON object. "
                    "Do not use markdown code blocks like ```json. "
                    f"Your JSON must strictly match this schema:\n{schema_str}"
                )
                messages.append({"role": "system", "content": sys_msg})

        messages.append({"role": "user", "content": str(prompt_text)})

        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        result_text = response.choices[0].message.content
        latency_ms = (time.time() - start) * 1000

        if schema:
            result_text = result_text.strip("` \n")
            if result_text.startswith("json\n"):
                result_text = result_text[5:]

        return GenerationResult(
            text=result_text,
            prompt_tokens=0,
            output_tokens=0,
            latency_ms=latency_ms,
            model=f"{model} (g4f fallback)"
        )
    except Exception as e:
        logger.error(f"G4F fallback failed: {e}")
        return None


def _run_fallback_chain(
    prompt: Any,
    schema: Optional[Any] = None,
) -> Optional[GenerationResult]:
    """Try fallback providers in order: Groq → g4f. Returns first success or None."""
    result = _groq_fallback(prompt, schema=schema)
    if result is not None:
        return result
    result = _fallback_generate(prompt, schema=schema)
    if result is not None:
        return result
    return None


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=2, min=3, max=30),
    reraise=True,
)
def generate(
    prompt: Any,
    schema: Optional[Any] = None,
    temperature: float = 0.2,
    model: str = DEFAULT_MODEL,
    tools: Optional[list] = None,
) -> GenerationResult:
    """
    Core generation call with rate limiting, multi-key failover, retry,
    token tracking, and timing.
    Raises ValueError if client is unavailable.
    Raises upstream SDK exceptions on API failure (after all keys exhausted).
    """
    if not _initialized:
        init_gemini()

    last_error = None
    key_attempts = 0
    max_key_attempts = max(len(_clients), 1) * 2

    _gemini_concurrency.acquire()
    try:
        while key_attempts < max_key_attempts:
            client = get_client()
            if client is None:
                fb = _run_fallback_chain(prompt, schema=schema)
                if fb is not None:
                    return fb
                raise ValueError(
                    f"Gemini client not available: {_init_error or 'Unknown error'}"
                )

            _rate_limiter.sync_wait_if_needed()

            config = types.GenerateContentConfig(
                temperature=temperature,
                safety_settings=SAFETY_SETTINGS,
            )
            if schema:
                config.response_mime_type = "application/json"
                config.response_schema = schema
            if tools:
                config.tools = tools

            try:
                start = time.time()
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=config,
                )
                latency_ms = (time.time() - start) * 1000

                prompt_tokens = 0
                output_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage = response.usage_metadata
                    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
                    output_tokens = getattr(usage, "candidates_token_count", 0) or 0

                return GenerationResult(
                    text=response.text if hasattr(response, "text") else "",
                    prompt_tokens=prompt_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    model=model,
                )
            except Exception as e:
                last_error = e
                error_msg = str(e)
                key_attempts += 1

            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                logger.warning(f"Rate limit on key {_current_key_index + 1}, cooling down for {KEY_COOLDOWN_SECONDS}s")
                _mark_key_cooldown(_current_key_index)
                _rotate_key()
                if len(_get_available_client_indices()) > 0:
                    continue
                logger.warning("All keys exhausted on rate limit, attempting fallback chain...")
                fb = _run_fallback_chain(prompt, schema=schema)
                if fb is not None:
                    return fb
                logger.error("All Gemini keys exhausted AND g4f fallback failed. Raising.")
                break
            else:
                _rotate_key()
                if len(_api_keys) > 1:
                    continue
                break
    finally:
        _gemini_concurrency.release()

    raise last_error or ValueError("All API keys exhausted")


async def async_generate(
    prompt: Any,
    schema: Optional[Any] = None,
    temperature: float = 0.2,
    model: str = DEFAULT_MODEL,
    tools: Optional[list] = None,
) -> GenerationResult:
    """
    Fully async version of generate().
    Uses async rate limiter directly — never blocks the event loop.
    Call this from async contexts instead of generate().
    """
    if not _initialized:
        init_gemini()

    last_error = None
    key_attempts = 0
    max_key_attempts = max(len(_clients), 1) * 2

    await asyncio.to_thread(_gemini_concurrency.acquire)
    try:
        while key_attempts < max_key_attempts:
            client = get_client()
            if client is None:
                fb = await asyncio.to_thread(_run_fallback_chain, prompt, schema=schema)
                if fb is not None:
                    return fb
                raise ValueError(
                    f"Gemini client not available: {_init_error or 'Unknown error'}"
                )

            await _rate_limiter.wait_if_needed()

            config = types.GenerateContentConfig(
                temperature=temperature,
                safety_settings=SAFETY_SETTINGS,
            )
            if schema:
                config.response_mime_type = "application/json"
                config.response_schema = schema
            if tools:
                config.tools = tools

            try:
                start = time.time()
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=prompt,
                    config=config,
                )
                latency_ms = (time.time() - start) * 1000

                prompt_tokens = 0
                output_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage = response.usage_metadata
                    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
                    output_tokens = getattr(usage, "candidates_token_count", 0) or 0

                return GenerationResult(
                    text=response.text if hasattr(response, "text") else "",
                    prompt_tokens=prompt_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    model=model,
                )
            except Exception as e:
                last_error = e
                error_msg = str(e)
                key_attempts += 1

                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                    logger.warning(f"Rate limit on key {_current_key_index + 1}, cooling down for {KEY_COOLDOWN_SECONDS}s")
                    _mark_key_cooldown(_current_key_index)
                    _rotate_key()
                    if len(_get_available_client_indices()) > 0:
                        continue
                    logger.warning("All keys exhausted on rate limit, attempting fallback chain...")
                    fb = await asyncio.to_thread(_run_fallback_chain, prompt, schema=schema)
                    if fb is not None:
                        return fb
                    logger.error("All Gemini keys exhausted AND fallback chain failed. Raising.")
                    break
                else:
                    _rotate_key()
                    if len(_api_keys) > 1:
                        continue
                break
    finally:
        await asyncio.to_thread(_gemini_concurrency.release)

    raise last_error or ValueError("All API keys exhausted")


async def async_generate_with_vision(
    contents: list,
    schema: Optional[Any] = None,
    temperature: float = 0.1,
    model: str = DEFAULT_MODEL,
) -> GenerationResult:
    """
    Fully async version of generate_with_vision().
    Uses async rate limiter directly.
    """
    if not _initialized:
        init_gemini()

    last_error = None
    key_attempts = 0
    max_key_attempts = max(len(_clients), 1) * 2

    await asyncio.to_thread(_gemini_concurrency.acquire)
    try:
        while key_attempts < max_key_attempts:
            client = get_client()
            if client is None:
                fb = await asyncio.to_thread(_run_fallback_chain, contents, schema=schema)
                if fb is not None:
                    return fb
                raise ValueError(
                    f"Gemini client not available: {_init_error or 'Unknown error'}"
                )

            await _rate_limiter.wait_if_needed()

            config = types.GenerateContentConfig(
                temperature=temperature,
                safety_settings=SAFETY_SETTINGS,
            )
            if schema:
                config.response_mime_type = "application/json"
                config.response_schema = schema

            try:
                start = time.time()
                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=model,
                    contents=contents,
                    config=config,
                )
                latency_ms = (time.time() - start) * 1000

                prompt_tokens = 0
                output_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage = response.usage_metadata
                    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
                    output_tokens = getattr(usage, "candidates_token_count", 0) or 0

                return GenerationResult(
                    text=response.text if hasattr(response, "text") else "",
                    prompt_tokens=prompt_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    model=model,
                )
            except Exception as e:
                last_error = e
                error_msg = str(e)
                key_attempts += 1

                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                    logger.warning(f"Rate limit on key {_current_key_index + 1}, cooling down for {KEY_COOLDOWN_SECONDS}s")
                    _mark_key_cooldown(_current_key_index)
                    _rotate_key()
                    if len(_get_available_client_indices()) > 0:
                        continue
                    fb = await asyncio.to_thread(_run_fallback_chain, contents, schema=schema)
                    if fb is not None:
                        return fb
                    logger.error("All Gemini keys exhausted AND fallback chain failed. Raising.")
                    break
                else:
                    _rotate_key()
                    if len(_api_keys) > 1:
                        continue
                    break
    finally:
        await asyncio.to_thread(_gemini_concurrency.release)

    raise last_error or ValueError("All API keys exhausted")


def generate_with_vision(
    contents: list,
    schema: Optional[Any] = None,
    temperature: float = 0.1,
    model: str = DEFAULT_MODEL,
) -> GenerationResult:
    """
    Vision-specific generation (multimodal content list).
    Same rate limiting, multi-key failover, and tracking as generate().
    """
    if not _initialized:
        init_gemini()

    last_error = None
    key_attempts = 0
    max_key_attempts = max(len(_clients), 1) * 2

    _gemini_concurrency.acquire()
    try:
        while key_attempts < max_key_attempts:
            client = get_client()
            if client is None:
                fb = _run_fallback_chain(contents, schema=schema)
                if fb is not None:
                    return fb
                raise ValueError(
                    f"Gemini client not available: {_init_error or 'Unknown error'}"
                )

            _rate_limiter.sync_wait_if_needed()

            config = types.GenerateContentConfig(
                temperature=temperature,
                safety_settings=SAFETY_SETTINGS,
            )
            if schema:
                config.response_mime_type = "application/json"
                config.response_schema = schema

            try:
                start = time.time()
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                latency_ms = (time.time() - start) * 1000

                prompt_tokens = 0
                output_tokens = 0
                if hasattr(response, "usage_metadata") and response.usage_metadata:
                    usage = response.usage_metadata
                    prompt_tokens = getattr(usage, "prompt_token_count", 0) or 0
                    output_tokens = getattr(usage, "candidates_token_count", 0) or 0

                return GenerationResult(
                    text=response.text if hasattr(response, "text") else "",
                    prompt_tokens=prompt_tokens,
                    output_tokens=output_tokens,
                    latency_ms=latency_ms,
                    model=model,
                )
            except Exception as e:
                last_error = e
                error_msg = str(e)
                key_attempts += 1

                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
                    logger.warning(f"Rate limit on key {_current_key_index + 1}, cooling down for {KEY_COOLDOWN_SECONDS}s")
                    _mark_key_cooldown(_current_key_index)
                    _rotate_key()
                    if len(_get_available_client_indices()) > 0:
                        continue
                    fb = _run_fallback_chain(contents, schema=schema)
                    if fb is not None:
                        return fb
                    logger.error("All Gemini keys exhausted AND fallback chain failed. Raising.")
                    break
                else:
                    _rotate_key()
                    if len(_api_keys) > 1:
                        continue
    finally:
        _gemini_concurrency.release()

    raise last_error or ValueError("All API keys exhausted")

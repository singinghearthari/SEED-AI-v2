# SEED AI — Project Information Document

## Project Overview

**SEED AI (Smart Ecosystem for Enhanced Agricultural Decisions)** is an autonomous Multi-Agent agricultural intelligence system built for the **Google AI Agents: Intensive Vibe Coding Capstone Project** (July 2026). It orchestrates multiple specialized AI agents powered by Google Gemini to help farmers with localized crop knowledge, disease detection, budget-aware treatment planning, weather risk analysis, and government scheme discovery.

**Track:** Agents for Good / Freestyle — Agricultural decision support using multi-agent AI

---

## 1. Problem Statement

Farmers face several interconnected challenges:
- Delayed identification of crop diseases
- Unpredictable weather affecting crop health
- Limited access to personalized agricultural guidance
- Fragmented information across multiple platforms
- Difficulty selecting treatments within budget
- Lack of continuous monitoring and follow-up
- Limited awareness of government subsidies and support schemes

Existing digital solutions address only one problem at a time, forcing farmers to manually combine diverse information sources into coherent decisions.

---

## 2. Solution

SEED AI introduces an **autonomous multi-agent ecosystem** where specialized AI agents collaborate to generate personalized farming decisions. Rather than functioning as a chatbot, the system:
- **Observes** (accepts text, voice, and image inputs)
- **Reasons** over multiple data sources
- **Plans** dynamically using Gemini Function Calling
- **Calls** external tools (weather APIs, market data, government databases)
- **Coordinates** up to 13 specialized AI sub-agents + memory + translation
- **Generates** action plans with budget optimization
- **Learns** from historical farm data via Firestore memory
- **Reflects** on decisions for safety and consistency
- **Streams** real-time execution via Server-Sent Events

---

## 3. Architecture

### 3.1 High-Level Architecture

```
Frontend (Next.js 16 + TypeScript + Tailwind CSS 4 + Framer Motion + shadcn/ui)
    |
    ├── SSE Client (ReadableStream, auth headers, circuit breaker)
    ├── Image Upload Component (drag-and-drop, preview)
    ├── Voice Input (Web Speech API, 11-language auto-detect)
    ├── Geolocation API + Nominatim reverse geocoding
    └── TTS (edge-tts backend + browser SpeechSynthesis fallback)
        |
    Backend (FastAPI + Python 3.10+)
        |
    Gemini Orchestrator Agent (1195 lines)
        |
        ├── Hybrid Vision Pipeline:
        │   ├── YOLO11 (local, 17 disease + 10 waste classes)
        │   ├── OpenRouter Gemma-4 26B (primary vision LLM)
        │   ├── Gemini Vision 2.0 Flash (fallback)
        │   ├── Qwen2.5-VL-7B-Instruct (HuggingFace expert analysis)
        │   └── HuggingFace models (ViT, MobileNetV2, SigLIP2)
        │
        ├── External Services:
        │   ├── OpenWeatherMap (live weather)
        │   ├── Data.gov.in Agmarknet (market prices)
        │   ├── Gemini API (11-key pool, round-robin, rate-limited)
        │   └── g4f GPT-4o (fallback when Gemini exhausted)
        │
        ├── EventBus (async batched persistence, 50 events/2s flush)
        ├── Dead Letter Queue (DLQ) for failed Firestore writes
        └── AgentEvaluator (per-user trace isolation, JSON logging)
```

### 3.2 Agent Architecture

The orchestrator dynamically selects and executes agents based on the user's query. Each agent specializes in a specific agricultural domain:

| # | Agent | Purpose | Category | Model/API |
|---|-------|---------|----------|-----------|
| 1 | **Vision Agent** | Leaf image disease diagnosis via hybrid vision pipeline | Analysis | YOLO11 + Gemma-4 + Gemini Vision |
| 2 | **Weather Agent** | Real-time weather & agricultural risk assessment | Analysis | OpenWeatherMap + Gemini schema |
| 3 | **Crop Knowledge Agent** | Disease info, treatment protocols, best practices | Analysis | Gemini + KB (RAG) |
| 4 | **Soil & Nutrient Agent** | Soil analysis, NPK recommendations, amendment guidance | Analysis | Gemini + soil_health KB |
| 5 | **Entomologist Agent** | Insect/pest identification and management (cultural/biological/chemical/organic) | Analysis | Gemini + pests KB |
| 6 | **Market Intelligence Agent** | Current prices, trends, selling recommendations | Prediction | Data.gov.in Agmarknet + Gemini |
| 7 | **Crop Prediction Agent** | Optimal crop selection (location/season/soil/budget) | Prediction | Gemini + crops KB |
| 8 | **Disease Prediction Agent** | Preventive disease modeling before symptoms appear | Prediction | Gemini + weather + diseases KB |
| 9 | **Budget Planning Agent** | Treatment cost estimation, budget optimization, cheapest vs best-value options | Planning | Gemini + treatments KB |
| 10 | **Government Scheme Agent** | Subsidy/insurance/scheme eligibility (PMFBY, PM-KISAN, KCC, etc.) | Planning | Government schemes KB |
| 11 | **Irrigation Agent** | Water scheduling, irrigation methods, moisture management | Planning | Gemini + weather + crops KB |
| 12 | **Waste-to-Wealth Agent** | Revenue from agricultural waste (compost, biochar, biofuel, SigLIP2 waste classification) | Planning | Gemini + HF SigLIP2 vision |
| 13 | **Task Planning Agent** | 7-day actionable farming schedule with priorities | Planning | Gemini |
| 14 | **Memory Agent** | Firestore-based persistent farm memory (6 actions + DLQ retry + caching) | Persistence | Firebase Firestore |
| 15 | **Translation Agent** | Multilingual support (Tamil, English, Hindi, etc.) | Communication | Gemini |

### 3.3 Tool Declarations (Gemini Function Calling)

The orchestrator registers 10 functions for Gemini Function Calling:

| Function | Maps to Agent | Purpose |
|----------|---------------|---------|
| `run_vision_analysis` | Vision Agent | Analyze crop leaf image |
| `run_weather_assessment` | Weather Agent | Fetch live weather |
| `run_market_analysis` | Market Agent | Market prices |
| `run_budget_planning` | Budget Agent | Treatment costs |
| `run_crop_knowledge_lookup` | Crop Knowledge Agent | Disease/treatment info |
| `run_government_scheme_search` | Government Scheme Agent | Govt subsidies |
| `run_task_scheduling` | Task Planning Agent | 7-day schedule |
| `run_crop_prediction` | Crop Prediction Agent | Optimal crops |
| `run_disease_prediction` | Disease Prediction Agent | Preventive disease prediction |
| `run_waste_to_wealth_analysis` | Waste-to-Wealth Agent | Waste revenue opportunities |

### 3.4 Execution Pipeline

1. **Request Intake** — Text, image (multipart upload, base64, or Supabase Storage), or voice input
2. **Cache Check** — md5 hash key, 300s TTL, max 100 entries (skipped for images)
3. **Image Upload** — MIME/10MB validation, Supabase Storage, 1hr signed URL
4. **Memory Retrieval** — Load farm profile from Firestore via MemoryAgent
5. **Zero Friction Context Inference** — Auto-fill missing location/crop/budget from:
   - Query text pattern matching (regex over KNOWN_LOCATIONS)
   - Historical farm memory from Firestore
   - Browser Geolocation API (reverse geocoded via Nominatim, 24h localStorage cache)
   - Sensible defaults (Bangalore, Tomato, ₹5000)
6. **Deterministic Routing** — Gemini Function Calling selects agents based on query
7. **Tier 1 Execution** — Concurrent `asyncio.gather` of core agents with 60s timeout, 2 retry attempts for transient errors (429, rate limit, timeout, quota)
8. **Decision Fusion** — LLM-based fusion into `FusionResult` (Gemini structured output with `LLMFusionSchema`); falls back to `_local_fusion()` (non-LLM)
9. **Guardrails** — Rain check (spray delay when rain_probability > 60%), budget ceiling (warning when total_cost > budget * 1.1, inject low-cost alternatives)
10. **Reflection** — Gemini self-check for budget compliance, spray safety, contradictions, safety
11. **Tier 2 (Fire-and-forget)** — Enrichment agents (government_schemes, waste_to_wealth, task_planning)
12. **Memory Persistence** — Batch commit via EventBus (farm_memory + conversation + execution_trace + disease_history)
13. **SSE Event Stream** — Real-time execution transparency to frontend
14. **Evaluation Trace** — Per-user `AgentEvaluator` records metrics

### 3.5 Execution Modes

| Mode | Description | Agents Used |
|------|-------------|-------------|
| **Auto** | AI-determined routing (default) | Tier 1 core + LLM-resolved specialists |
| **Fast Track** | Quick disease diagnosis | vision, disease_prediction |
| **Ensemble** | 5-agent coordinated swarm | soil_nutrient, weather, crop_knowledge, disease_prediction, market |
| **Specific** | Single designated specialist | User-selected agent |
| **All (Swarm)** | Full end-to-end simulation | All 13 agents |

### 3.6 Agent Routing Logic

- **Vision Bypass**: Image present → `["vision", "disease_prediction"]`
- **Market Shortcut**: Keywords (price, mandi, market, cost, sell) → `["market"]`
- **Fast Track**: `execution_mode="fast_track"` → `["disease_prediction"]`
- **Specific**: `execution_mode="specific"` → `[specific_agent]`
- **All**: `execution_mode="all"` → all agents
- **Ensemble**: core + disease_prediction + market
- **Auto (default)**: Tier 1 core (crop_knowledge, weather, soil_nutrient, budget) + market (always) + LLM-resolved specialists (vision, entomologist, irrigation, etc.)

### 3.7 MCP Server (Model Context Protocol)

A standalone MCP server at `mcp_server/` exposes the knowledge bases as interoperable tools via the Model Context Protocol standard:

| Tool | Description | Returns |
|------|-------------|---------|
| `get_disease_info` | Search diseases by name or affected crop | Symptoms, risk, yield loss, spread, regions |
| `get_treatment_plan` | Get treatment options for a disease | Costs, dosages, effectiveness, waiting period |
| `get_crop_guide` | Get agronomic info for a crop | Season, soil, water, pests, varieties, yield |
| `find_government_schemes` | Search government schemes by name/type | Eligibility, benefits, premiums, application |
| `get_pest_management` | Search pests by name or crop | ID, lifecycle, threshold, controls (4 types) |
| `get_soil_guide` | Get soil type information | Coverage, pH, nutrients, best crops, management |
| `get_market_prices` | MSP data for Indian crops | MSP per quintal, cost of production |
| `knowledge_base_categories` | List all KB categories | 8 category names |

**Resources** (static data URIs):
- `seedai://diseases/list`, `seedai://crops/list`, `seedai://schemes/list`, `seedai://pests/list`

**Run:** `python mcp_server/server.py --transport stdio` (CLI) or `--transport sse` (HTTP). Uses `mcp` SDK v1.28+. All 8 tools verified working via `ClientSession`. Test with: `python mcp_server/test_mcp.py`

### 3.8 Tier Definitions

- **TIER1_CORE** = `{"crop_knowledge", "weather", "soil_nutrient", "budget"}`
- **TIER2_ENRICHMENT** = `{"government_schemes", "waste_to_wealth", "task_planning"}`
- **NON_CRITICAL_AGENTS** = `{"market", "government_schemes", "task_planning", "crop_prediction", "disease_prediction", "waste_to_wealth"}`
- Agent timeout: 60 seconds
- Retry attempts: 2 (transient errors: 429, rate limit, timeout, quota, connection)

---

## 4. Technology Stack

### 4.1 Frontend
- **Framework**: Next.js 16.2.9 (App Router, static export `output: 'export'`)
- **Language**: TypeScript 5 (strict mode)
- **Styling**: Tailwind CSS 4, tw-animate-css, shadcn/ui (base-nova style)
- **Animation**: Framer Motion 12.42.0
- **UI Components**: shadcn/ui (20+ components), Lucide React 1.21.0 icons
- **Charts**: Recharts 3.9.1
- **State**: React Context + hooks (50+ state variables in simulator)
- **SSE**: Fetch API with ReadableStream, circuit breaker pattern, auth headers
- **Voice Input**: Web Speech API (webkitSpeechRecognition) with 11-language auto-detect
- **TTS**: Backend edge-tts (primary) + Browser SpeechSynthesis (fallback)
- **Geolocation**: Browser Geolocation API + Nominatim reverse geocoding
- **Build**: ESLint 9, PostCSS with @tailwindcss/postcss
- **MCP Server**: `mcp` SDK v1.28+ — 8 KB tools + 4 resources, stdio/SSE transport
- **Performance**: React.memo, useMemo, useCallback, optimized package imports, throttled event flusher (50ms debounce)
- **Auth Token Refresh**: 50-minute background interval via Firebase SDK

### 4.2 Backend
- **Framework**: FastAPI (Python 3.10+) with `lifespan` context manager
- **AI/ML**:
  - Google Gemini API (`google-genai` SDK) — model: `gemini-2.5-flash`
  - Multi-key pool: up to 11 keys (GEMINI_API_KEY, GEMINI_API_KEY1–10), round-robin load balancing
  - Key cooldown: 30s blacklist on 429 errors
  - Concurrency control: Semaphore (dynamically scaled to key count)
  - Fallback LLM: g4f (GPT-4o) when all Gemini keys exhausted
  - Tenacity retry: 4 attempts, exponential backoff (2–30s), 429-aware
  - MCP Server: `mcp` SDK v1.28+ — standalone MCP server at `mcp_server/`, 8 tools + 4 resources, stdio/SSE transport
- **Rate Limiting**: Async token-bucket rate limiter
  - Default: 4 RPM (safe margin under 5 RPM free tier)
  - Per-key: 15 RPM
  - Sliding 60s window + minimum interval enforcement
- **Vision Pipeline (Hybrid)**:
  - YOLO11 (local, model: yolo11n.pt, ultralytics) — 17 disease classes + 10 waste classes
  - OpenRouter (Gemma-4 26B A4B IT, free tier) — primary LLM vision analysis
  - Gemini Vision 2.0 Flash — fallback when OpenRouter fails
  - Qwen2.5-VL-7B-Instruct (via HuggingFace Inference API) — expert disease/waste analysis
  - HuggingFace serverless: ViT crop_leaf_diseases, MobileNetV2 plant-disease, SigLIP2 waste classifier
- **Database**: Firebase Firestore (farm_memory, conversation_history, disease_history, execution_logs, dlq_events)
- **Storage**: Supabase Storage (leaf-images bucket, auto-create, 1hr signed URLs)
- **Authentication**: Firebase Auth (anonymous, email/password, Google OAuth)
- **External APIs**: OpenWeatherMap, Data.gov.in Agmarknet
- **TTS**: edge-tts (12 languages, local file cache with SHA-256 keys)
- **EventBus**: In-process async event bus with batched persistence (2s flush interval, 50 batch size, max 5000 queue)
- **Dead Letter Queue**: Retry dead-lettered Firestore writes (max 3 attempts)
- **Logging**: Structured JSON logging (4 rotating handlers: console, seed_ai.log, errors.log, execution_traces.log)
- **Testing**: pytest, pytest-asyncio
- **Middleware**: CORS (localhost:3000/3001), Firebase token verification (require_auth, optional_auth)

### 4.3 Knowledge Base (JSON files — 8 files)

| File | Entries | Size | Purpose |
|------|---------|------|---------|
| `crops.json` | 8 crops | 178 lines | Tomato, Rice, Wheat, Cotton, Potato, Onion, Mango, Sugarcane with full agronomic data |
| `diseases.json` | 15 diseases | 302 lines | Early Blight → Sheath Blight, symptoms, causes, spread, yield loss 20–100% |
| `treatments.json` | 12 disease sets | 464 lines | 40+ treatments (chemical/organic/biological/cultural), dosages, costs, brands |
| `fertilizers.json` | 8 fertilizers | 142 lines | Urea, DAP, MOP, NPK Complex, SSP, ZnSO4, Vermicompost, Neem Coated Urea |
| `pests.json` | 6 pests | 146 lines | Whitefly, Helicoverpa, BPH, Fall Armyworm, Aphids, Pink Bollworm |
| `soil_health.json` | 5 soil types | 147 lines | Alluvial (43%), Black (24%), Red (18%), Laterite (8%), Saline-Sodic (3%) |
| `government_schemes.json` | 10 schemes | 230 lines | PMFBY, PM-KISAN, KCC, Soil Health Card, PMKSY, e-NAM, Maandhan, AIF, PKVY, SMAM |
| `market_intelligence.json` | 3 sections | 68 lines | MSP for 26 crops, 8 major mandis, volatility index (Tomato: Very High) |

### 4.4 Key Backend Files

| File | Lines | Purpose |
|------|-------|---------|
| `agents/orchestrator_agent.py` | 1195 | Central orchestrator — routing, execution, fusion, reflection, caching |
| `services/gemini_service.py` | 792 | Multi-key Gemini client, rate limiter, g4f fallback |
| `api/routes.py` | 622 | All REST API endpoints |
| `agents/base_agent.py` | 207 | Abstract base with Gemini calls, sanitization, timing |
| `agents/memory_agent.py` | 317 | Firestore persistence with caching, DLQ |
| `services/event_bus.py` | 154 | Async batched event bus |
| `services/hf_vision_analyzer.py` | 160 | HuggingFace serverless (ViT, MobileNetV2, SigLIP2) |
| `services/yolo_detector.py` | 195 | YOLO11 local detection (CUDA/MPS/CPU auto-detect) |
| `services/hybrid_vision_service.py` | 99 | Orchestrates OpenRouter → Gemini Vision pipeline |
| `services/qwen_vision_service.py` | 165 | Qwen2.5-VL expert analysis via HuggingFace |
| `services/openrouter_service.py` | 131 | OpenRouter Gemma-4 API integration |
| `services/tts_service.py` | 258 | edge-tts with caching, 12 languages |
| `services/firebase_service.py` | 137 | Firebase Admin SDK, cached token verification |
| `services/storage_service.py` | 133 | Supabase Storage (MIME validation, 10MB limit) |
| `services/persistence_handler.py` | 62 | EventBus → MemoryAgent bridge |
| `services/bus.py` | 28 | EventBus singleton accessor |
| `api/orchestration.py` | 112 | SSE streaming orchestration endpoints |
| `api/tts_routes.py` | 113 | TTS generation, caching, language detection |
| `evaluation/benchmark.py` | 233 | Per-user trace isolation, reports |
| `models/schemas.py` | 138 | All Pydantic models (AgentResult, FusionResult, etc.) |
| `middleware/__init__.py` | — | require_auth, optional_auth FastAPI dependencies |
| `utils/api_gateway.py` | — | HTTP retry wrapper (3 attempts, 2–10s backoff) |
| `utils/dataset_manager.py` | — | Knowledge base indexer (keyword matching, RAG) |
| `utils/logger.py` | — | Structured JSON logging (4 handlers, rotation) |
| `main.py` | 143 | FastAPI entry, config validation, EventBus lifecycle |
| `tests/test_api.py` | 188 | 19 tests: health, knowledge, orchestrate, agents, sanitization, dataset |

### 4.5 Key Frontend Files

| File | Lines | Purpose |
|------|-------|---------|
| `src/app/page.tsx` | 2357 | Main Simulator (Command Center) — SSE, swarm viz, results, voice, TTS, presets |
| `src/app/activity/page.tsx` | 519 | Real-time agent execution event feed (SSE + polling) |
| `src/app/analytics/page.tsx` | 517 | Performance charts, KPIs, execution telemetry |
| `src/app/dashboard/page.tsx` | 387 | System overview, agent fleet, capability matrix, live traces |
| `src/app/timeline/page.tsx` | 452 | 7-day farming schedule with task checkoff and progress |
| `src/app/history/page.tsx` | 429 | Past queries with pagination, search, filter, confidence badges |
| `src/components/auth-screen.tsx` | 265 | Login/signup with Google OAuth, animated showcase |
| `src/components/client-layout.tsx` | 282 | Navbar, auth gating, dark mode, command palette, mobile drawer |
| `src/components/command-palette.tsx` | 146 | ⌘K quick navigation with number shortcuts |
| `src/components/data-loader.tsx` | 122 | Universal loading/error/empty state (15s timeout, skeleton) |
| `src/components/speak-button.tsx` | 235 | TTS controls with waveform visualization |
| `src/components/error-boundary.tsx` | 66 | React error boundary with retry |
| `src/lib/api.ts` | 294 | HTTP client + SSE with circuit breaker (4 URLs, 3 fail threshold, 30s cooldown) |
| `src/lib/auth-context.tsx` | 150 | Firebase auth provider (50-min token refresh) |
| `src/lib/firebase.ts` | 36 | Firebase singleton with hot-reload guard |
| `src/hooks/use-speech-recognition.ts` | 222 | Web Speech API with 11-language auto-detect |
| `src/hooks/use-text-to-speech.ts` | 351 | Dual TTS (backend edge-tts + browser fallback) |
| `src/app/globals.css` | 343 | Full theme (light/dark), glass morphism, neon glow, grid patterns, animations |

---

## 5. API Endpoints

### 5.1 Core Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /` | GET | None | Root status, version, Gemini/HF availability |
| `GET /api/health` | GET | None | Service status, 16 agents, knowledge bases, features |
| `GET /api/health/deep` | GET | None | Deep health with live Gemini API ping |
| `GET /api/health/connectivity` | GET | None | EventBus, Firestore write, Gemini connectivity |
| `GET /api/diagnostics` | GET | None | Configuration diagnostics (no secrets) |

### 5.2 Orchestration Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `POST /api/orchestrate` | POST | Required | Text query → SSE event stream |
| `POST /api/orchestrate/upload` | POST | Required | Multipart image + text → SSE event stream |

**OrchestrateRequest**: user_id, text_query, image_base64 (optional), location, budget, crop, execution_mode (auto/fast_track/ensemble/specific/all), specific_agent

### 5.3 Knowledge Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /api/knowledge/{category}` | GET | None | Full knowledge base category (diseases, crops, treatments, etc.) |

### 5.4 History Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /api/history/{user_id}` | GET | Optional | Paginated conversation history (page/limit/sort/search/confidence) |
| `GET /api/history/me` | GET | Required | Authenticated user's history |

### 5.5 Evaluation Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /api/evaluation/traces` | GET | Required | Execution traces from Firestore or in-memory evaluator |
| `GET /api/trends` | GET | Required | Aggregated execution trends (daily grouping) |
| `GET /api/anomalies` | GET | Required | Latency anomaly detection (2-sigma, configurable lookback) |

### 5.6 Real-Time Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /api/activity/stream` | GET | Optional | SSE stream for live execution events via EventBus |

### 5.7 Vision Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `POST /api/vision/analyze` | POST | Required | Hybrid vision analysis (YOLO11 + Qwen2.5-VL), modes: disease/waste |
| `GET /api/vision/status` | GET | None | Vision pipeline component status |

### 5.8 TTS Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `GET /api/tts/languages` | GET | None | 12 supported languages with native names |
| `GET /api/tts/voices` | GET | None | 29 voices, filterable by language |
| `POST /api/tts/detect` | POST | None | Language detection via Unicode script analysis |
| `POST /api/tts/generate` | POST | None | Generate TTS audio (text, voice, rate, language) |
| `GET /api/tts/audio/{cache_key}` | GET | None | Serve cached audio (immutable cache headers) |
| `POST /api/tts/cache/clear` | POST | None | Clear expired TTS cache entries |

### 5.9 Auth Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `POST /api/auth/verify` | POST | None | Firebase ID token verification |

---

## 6. SSE Event Types (Streaming)

| Type | Phase | Description |
|------|-------|-------------|
| `event` | any | Real-time agent execution step with message, agent name, latency, tools |
| `pre_result` | fusion | Tier-1 decision fusion ready |
| `result` | complete | Final FusionResult with agent metadata, execution report |
| `error` | error | Error with degraded fallback result |

---

## 7. Pydantic Schemas

### 7.1 Agent Status Codes

| Status | Description |
|--------|-------------|
| `SUCCESS` | Agent completed successfully |
| `FAILED` | Agent failed with error |
| `SKIPPED` | Agent not required for this query |
| `TIMEOUT` | Agent exceeded 60s timeout |
| `CONFIGURATION_ERROR` | Missing credentials/config |
| `RETRYING` | Agent retrying after transient error |
| `RUNNING` | Agent currently executing |

### 7.2 AgentResult
- `status` (AgentStatus), `agent_name`, `execution_time_ms`, `tool_calls`, `tokens_used`
- `confidence` (0.0–1.0), `reasoning`, `error`, `data` (dict), `retries`, `model`, `timestamp`
- `.succeeded` property

### 7.3 FusionResult
- `summary`, `recommended_actions` (list), `confidence_score`, `confidence_label`
- `risk_level` (Low/Medium/High), `budget_assessment`, `weather_consideration`
- `evidence_sources`, `agents_used` (list), `tools_executed` (list)
- `alternatives_considered`, `government_schemes`, `follow_up_actions`
- `is_degraded`, `failed_agents`, `degradation_reasons`
- `confidence_to_label()`: 90–100 → High, 75–89 → Medium, <75 → Low

### 7.4 ExecutionReport
- `report_title`, `generated_at`, `request_id`, `trace_id`, `query`
- `location`, `crop`, `budget`, `execution_mode`, `total_latency_ms`, `total_tokens`
- `agents_executed`, `agents_succeeded`, `agents_failed`
- `fusion_result`, `agent_results`, `agent_metadata`, `performance_metrics`
- `execution_log`, `is_degraded`, `status`

---

## 8. Firestore Schema

### 8.1 Collections

| Collection | Document ID | Key Fields | Indexes |
|------------|-------------|------------|---------|
| `farm_memory` | `{userId}` | user_id, crop, location, last_query, last_recommendation, updated_at | None needed |
| `conversation_history` | Auto | user_id, query, recommendation, agents_used, confidence, timestamp | user_id+timestamp DESC, user_id+confidence+timestamp DESC |
| `disease_history` | Auto | user_id, disease, crop, severity, confidence, image_path, timestamp | user_id+timestamp DESC |
| `execution_logs` | Auto | trace_id, user_id, total_latency_ms, status, agents_invoked[], confidence_score, timestamp | user_id+timestamp DESC, user_id+confidence_score+timestamp DESC |
| `dlq_events` | Auto | retry_count, failed_at, payload | retry_count+failed_at ASC |

### 8.2 Security Rules (firestore.rules)

- `farm_memory/{userId}`: `request.auth.uid == userId`
- `conversation_history/{docId}`: `resource.data.user_id == request.auth.uid`
- `execution_logs/{docId}`: `resource.data.user_id == request.auth.uid`
- `disease_history/{docId}`: `resource.data.user_id == request.auth.uid`
- Default deny: `match /{document=**} { allow read, write: if false; }`

---

## 9. Frontend Architecture

### 9.1 Pages (6)

| Page | Route | Lines | Purpose |
|------|-------|-------|---------|
| Simulator | `/` | 2357 | Main command center — SSE, swarm viz, 6 result tabs, presets, voice, TTS |
| Dashboard | `/dashboard` | 387 | KPIs, agent fleet grid, capability matrix, live SSE traces, latency chart |
| Activity | `/activity` | 519 | Real-time event feed (SSE + polling), search, filter, export |
| Analytics | `/analytics` | 517 | Charts (confidence pie, agent success bars, latency bars), telemetry |
| Timeline | `/timeline` | 452 | 7-day schedule generation, task checkoff, progress bar, export |
| History | `/history` | 429 | Paginated conversation browser, search, confidence filter, export JSON |

### 9.2 Simulator Page Features

- **Swarm SVG Visualization**: 16 agent nodes with animated connection lines, running indicator (animated dash), orbital particles, hover tooltips (status/latency/confidence)
- **Event Log Terminal**: macOS terminal (red/yellow/green dots), search, filter (all/success/failed), expandable details, infinite scroll (100 per batch), export trace log
- **Results Tabs (6)**: Action Plan, 7-Day Timeline, Weather & Irrigation, Soil & Health, Markets & Schemes, Waste Utilization
- **Voice Input**: Mic button with 11-language auto-detect (`SpeechRecognition` with sequential language fallback)
- **TTS Integration**: Sentence highlighting, auto-play toggle, 10-language selector, sentence counter
- **Geolocation**: Auto-detect via browser API + Nominatim (24h localStorage cache, 26 known Indian cities)
- **Client-Side Field Inference**: Regex parsing for location, crop, budget from query text
- **Image Upload**: Drag-and-drop + click-to-browse, preview with delete
- **Execution Mode Selector**: 5 modes with animated `layoutId="modeBg"` indicator
- **Preset System**: 5 clickable presets (Tomato Blight, Rice Irrigation, Budget Planning, Weather Check, Swarm Simulation)
- **Advanced Options**: Soil type, farm size dropdowns, AI reasoning profile
- **Timeout Handling**: 180s AbortController, rate-limit suggestion messages
- **Report Export**: Copy summary, download text report, download JSON report
- **Performance**: React.memo (AgentNode, ProgressIndicator, EventLog, ReportActions, PerformanceMetrics), useMemo for derived data, useCallback for handlers, refs for stale closure avoidance
- **Throttled Event Flusher**: 50ms debounce between state updates

### 9.3 SSE Frontend Implementation

- `createSSEStream()` / `createSSEStreamWithAuth()` in `lib/api.ts`
- Direct `response.body.getReader()` consumption (not EventSource API — auth header support)
- Circuit breaker: 4 failover URLs, 3 failure threshold, 30s cooldown
- 120s default timeout
- `data:` lines parsed as JSON events
- Dashboard/Activity/Analytics: `SSE /api/activity/stream` → `new_traces` events, fallback to 10–15s polling

### 9.4 Authentication Flow

1. **Firebase Init**: Singleton `getApps().length` guard, Firebase config in env vars
2. **AuthProvider**: `onAuthStateChanged` listener, background token refresh every 50min
3. **AuthScreen**: Email/password login + register, Google OAuth popup, animated showcase cards
4. **ClientLayout**: Loading spinner → AuthScreen → app content; dark mode toggle (localStorage); scroll-aware navbar; mobile drawer

### 9.5 UI Components (shadcn/ui, 20+)

| Component | Type | Features |
|-----------|------|----------|
| button | base-ui | 6 variants, 8 sizes (xs→icon-lg), rounded-xl |
| badge | base-ui | 6 variants, rounded-4xl |
| card | Layout | 7 sub-components, CSS variable spacing |
| dialog | base-ui | Modal with backdrop blur, 7 sub-components |
| sheet | base-ui/dialog | 4 sides (top/right/bottom/left) |
| dropdown-menu | base-ui/menu | Full menu system (groups, submenus, checkboxes, radio) |
| select | base-ui/select | With scroll buttons, groups |
| tabs | base-ui/tabs | 2 variants (default/line), animated indicator |
| tooltip | base-ui/tooltip | Configurable delay, arrow positioning |
| progress | base-ui/progress | Label track indicator with value |
| kpi-card | Custom | Memoized metric card with icon, color, change indicator |
| animated-counter | Custom | requestAnimationFrame counting, cubic ease-out |
| input | base-ui | Focus ring, disabled, dark mode |
| textarea | Custom | field-sizing-content auto-height |
| avatar | base-ui | Image/fallback/badge/group/count |
| skeleton | Custom | Animated pulse placeholder |
| separator | base-ui | Horizontal/vertical |
| page-transition | Custom | AnimatePresence fade + slide |

---

## 10. Hybrid Vision Pipeline (Detailed)

```
Input Image
    │
    ▼
┌─────────────────────────────────────────────┐
│ 1. YOLO11 Detection (local, yolo11n.pt)      │
│    • 17 disease classes + 10 waste classes    │
│    • Bounding boxes + annotated image (base64) │
│    • CUDA → MPS → CPU auto-detect              │
│    • Configurable confidence (0.25) / IoU (0.45)│
│    • Inference time tracked                    │
└─────────────────────────────────────────────┘
    │ detections + annotated image
    ▼
┌─────────────────────────────────────────────┐
│ 2. OpenRouter Vision (PRIMARY)               │
│    • Model: google/gemma-4-26b-a4b-it:free   │
│    • Structured JSON analysis of leaf image   │
│    • 30s timeout                              │
│    • Base64 inline image in message           │
└─────────────────────────────────────────────┘
    │ SUCCESS → expert_analysis, expert_model
    │ FAILURE → fallback
    ▼
┌─────────────────────────────────────────────┐
│ 3. Gemini Vision 2.0 Flash (FALLBACK)        │
│    • Multimodal content (text + image)        │
│    • Disease, severity, confidence             │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 4. Qwen2.5-VL-7B-Instruct (Optional Expert)  │
│    • Via HuggingFace Inference API            │
│    • Disease mode / Waste mode                │
│    • Structured analysis with latency         │
└─────────────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────────────┐
│ 5. HuggingFace Serverless Models             │
│    • ViT: wambugu71/crop_leaf_diseases_vit   │
│    • MobileNetV2: Daksh159/plant-disease-... │
│    • SigLIP2: prithivMLmods/...waste...      │
│    • 2s/4s retry on 503 (cold-start)         │
└─────────────────────────────────────────────┘
```

---

## 11. Gemini Rate Limiting Architecture

```
Gemini Request
    │
    ├─ Threading.Semaphore (concurrency cap = N keys)
    ├─ AsyncRateLimiter (4 RPM default, 15 RPM per key)
    │   └─ Sliding window (60s) + minimum interval
    │
    ├─ Multi-Key Pool (11 keys max, round-robin)
    │   ├─ On 429: mark key COOLDOWN (30s) → rotate
    │   └─ All keys exhausted → g4f fallback
    │
    └─ tenacity retry (4 attempts, exponential backoff 2–30s)
```

---

## 12. Persistence Flow

```
Orchestrator → EventBus.emit("persist", {type, action, payload})
                   │
              Consumer Loop (every 2s or every 50 events)
                   │
              FirestorePersistenceHandler.__call__(batch)
                   │
                   ├─ "persist" → MemoryAgent._batch_persist()
                   │   ├─ farm_memory (upsert by userId)
                   │   ├─ conversation_history (new doc)
                   │   ├─ execution_logs (new doc)
                   │   └─ disease_history (new doc, conditional)
                   │
                   ├─ "persist_single" → MemoryAgent._persist_single()
                   │
                   └─ ON FAILURE → DLQ (dead letter queue)
                       ├─ retry_count + 1
                       ├─ max 3 attempts
                       └─ stored in dlq_events collection
```

---

## 13. Key Features

### 13.1 Zero Friction Context Inference
Missing fields (location, crop, budget) are automatically inferred from:
- Query text pattern matching (26 known Indian cities, regex crop detection, INR/digit budget detection)
- Historical farm memory from Firestore
- Browser Geolocation API (Nominatim reverse geocoding, 24h localStorage cache)
- Sensible defaults (Bangalore, Tomato, ₹5000)

### 13.2 Decision Fusion & Reflection
- **Fusion**: Merges all successful agent outputs into a coherent `FusionResult` using Gemini structured output (`LLMFusionSchema`); falls back to `_local_fusion()` (non-LLM aggregation)
- **Guardrails**: Rain check (spray delay when rain_probability > 60%), budget ceiling (warning when total_cost > budget * 1.1, inject low-cost alternatives)
- **Reflection**: Critiques the fusion for safety (budget compliance, spray safety vs rain, contradictions) and revises if needed
- **Confidence**: Weighted average of agent confidences, penalized for failed agents

### 13.3 Graceful Degradation
- If critical agents fail (vision, weather, crop_knowledge, budget), fusion is skipped with degraded result
- Non-critical agents (market, gov_schemes, task_planning, crop_prediction, disease_prediction, waste_to_wealth) can fail without blocking results
- Missing credentials disable specific features but core LLM orchestration continues

### 13.4 Real-Time Execution Transparency
Server-Sent Events (SSE) stream live execution steps, agent latencies, tools used, and status to the frontend dashboard in real-time. Frontend displays in a macOS-style terminal with search, filter, and expandable events.

### 13.5 Internal Caching
- Orchestrator caches results by md5 hash of (query + location + crop + budget + execution_mode + specific_agent + has_image)
- 300s TTL, max 100 entries
- Cache skipped for image queries

### 13.6 Prompt Injection Sanitization
BaseAgent sanitizes 5 injection patterns: "ignore all previous instructions", "forget all previous instructions", "you are now a", "new instructions:", "system:", `<system>` tags

### 13.7 Multi-Key Gemini Pool
- Supports up to 11 API keys (GEMINI_API_KEY + GEMINI_API_KEY1–10)
- Round-robin client selection
- 30s key cooldown on 429 errors
- Dynamic rate limit (4 RPM default, 15 RPM per key)
- Concurrency semaphore scaled to key count

### 13.8 Fallback LLM (g4f)
When all Gemini API keys are exhausted (429/quota), the system falls back to g4f (free tier GPT-4o) as an unlimited fallback for sync `generate()` calls.

### 13.9 Multi-User Data Isolation
- **Authentication**: Firebase Auth (anonymous, email/password, Google OAuth)
- **Backend**: `require_auth` FastAPI dependency verifies Firebase ID tokens from Bearer headers
- **Frontend**: `auth-context.tsx` provides getAuthToken(), `createSSEStreamWithAuth` attaches Bearer tokens (not query params)
- **In-Memory**: `AgentEvaluator.trace_data` is a per-user `Dict[str, list]` (not shared global list)
- **Database**: Firestore security rules enforce `request.auth.uid == userId` for all collections
- **Token Refresh**: Background refresh every 50 minutes

### 13.10 Circuit Breaker (Frontend API)
- 4 backup URLs (localhost:8000, 127.0.0.1:8000, localhost:8001)
- FAILURE_THRESHOLD = 3 — opens circuit after 3 failures
- COOLDOWN_MS = 30000 — 30s before retry

### 13.11 Speech Recognition
- 11 Indian languages: Auto, Hindi, English, Bengali, Tamil, Telugu, Malayalam, Kannada, Gujarati, Marathi, Urdu
- Auto-detect mode: tries languages sequentially from priority order (hi-IN → en-IN → ta-IN → ...)
- Continuous recognition with interim results
- Final transcript building via ref

### 13.12 Text-to-Speech
- 10 supported languages with native names
- Dual strategy: Backend edge-tts (primary, with audio caching) → Browser SpeechSynthesis (fallback)
- Sentence-by-sentence reading with `onSentenceChange` callback
- Language-specific voice selection via `LANG_TO_BROWSER_VOICE_PREF`
- Backend: 12 languages, 29 voices, SHA-256 cached audio, immutable cache headers

---

## 14. Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Required | Google Gemini API key |
| `GEMINI_API_KEY1`–`10` | Optional | Additional Gemini keys (round-robin) |
| `OPENROUTER_API_KEY` | Optional | OpenRouter (Gemma-4 vision fallback) |
| `HUGGING_FACE_API` | Optional | HuggingFace Inference API (vision models) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Required | Firebase Admin SDK JSON path |
| `OPENWEATHER_API_KEY` | Optional | OpenWeatherMap (weather agent) |
| `DATA_GOV_IN_API_KEY` | Optional | Data.gov.in Agmarknet (market agent) |
| `SUPABASE_URL` | Optional | Supabase project URL |
| `SUPABASE_SERVICE_ROLE_KEY` | Optional | Supabase admin key |
| `SUPABASE_BUCKET` | Optional | Default: leaf-images |
| `NEXT_PUBLIC_FIREBASE_API_KEY` | Required | Firebase client API key |
| `NEXT_PUBLIC_FIREBASE_APP_ID` | Required | Firebase app ID |
| `DATASET_PATH` | Optional | Local ML dataset path |

---

## 15. Deployment

### 15.1 Local Development
- **Backend**: `uvicorn main:app --reload --port 8000` (from `backend/`)
- **Frontend**: `npm run dev` (from `frontend/`, port 3000)

### 15.2 Test Commands
- **Backend**: `python -m pytest backend/tests/`
- **Frontend**: `npm run lint` (from `frontend/`)

### 15.3 Target Platforms
- Frontend: Vercel / Firebase Hosting (static export from `frontend/out/`)
- Backend: Cloud Run / local server
- Database: Firebase Firestore (project: seed-ai-capstone-project)
- Storage: Supabase Storage (bucket: leaf-images)
- Auth: Firebase Authentication

### 15.4 Firebase Configuration
- **Hosting**: `frontend/out/`, clean URLs, client-side rewrite
- **Firestore**: 6 composite indexes, version 2 security rules
- **Default project**: `seed-ai-capstone-project`
- **Ignored in git**: `*.env`, `*-adminsdk-*.json`, `serviceAccountKey*.json`, `logs/`

---

## 16. File Structure

```
C:\TrustisM\Capstone Project\
├── backend/
│   ├── main.py                    # FastAPI entry point (143 lines)
│   ├── .env                       # Backend env vars
│   ├── requirements.txt           # Python dependencies
│   ├── yolo11n.pt                 # YOLO11 model weights
│   ├── agents/
│   │   ├── orchestrator_agent.py  # Core orchestrator (1195 lines)
│   │   ├── base_agent.py          # Base agent class (207 lines)
│   │   ├── vision_agent.py        # Hybrid vision pipeline (91 lines)
│   │   ├── weather_agent.py       # OpenWeatherMap + Gemini (68 lines)
│   │   ├── market_intelligence_agent.py (69 lines)
│   │   ├── budget_planning_agent.py (73 lines)
│   │   ├── crop_knowledge_agent.py (65 lines)
│   │   ├── disease_prediction_agent.py (89 lines)
│   │   ├── crop_prediction_agent.py (81 lines)
│   │   ├── government_scheme_agent.py (70 lines)
│   │   ├── task_planning_agent.py (68 lines)
│   │   ├── waste_to_wealth_agent.py (111 lines)
│   │   ├── soil_nutrient_agent.py (73 lines)
│   │   ├── entomologist_agent.py (64 lines)
│   │   ├── irrigation_agent.py (71 lines)
│   │   ├── memory_agent.py        # Firestore persistence (317 lines)
│   │   └── translation_agent.py   (64 lines)
│   ├── api/
│   │   ├── routes.py              # REST endpoints (622 lines)
│   │   ├── orchestration.py       # SSE orchestration (112 lines)
│   │   └── tts_routes.py          # TTS endpoints (113 lines)
│   ├── services/
│   │   ├── gemini_service.py      # Multi-key Gemini + rate limiter (792 lines)
│   │   ├── firebase_service.py    # Firebase Admin SDK (137 lines)
│   │   ├── storage_service.py     # Supabase Storage (133 lines)
│   │   ├── weather_service.py     # OpenWeatherMap (38 lines)
│   │   ├── market_service.py      # Data.gov.in (50 lines)
│   │   ├── tts_service.py         # edge-tts + caching (258 lines)
│   │   ├── event_bus.py           # Async batched event bus (154 lines)
│   │   ├── bus.py                 # EventBus singleton (28 lines)
│   │   ├── persistence_handler.py # EventBus→Firestore bridge (62 lines)
│   │   ├── hybrid_vision_service.py # OpenRouter→Gemini pipeline (99 lines)
│   │   ├── openrouter_service.py  # Gemma-4 API (131 lines)
│   │   ├── qwen_vision_service.py # Qwen2.5-VL expert analysis (165 lines)
│   │   ├── hf_vision_analyzer.py  # HuggingFace serverless vision (160 lines)
│   │   └── yolo_detector.py       # YOLO11 local detection (195 lines)
│   ├── models/
│   │   └── schemas.py             # AgentResult, FusionResult, etc. (138 lines)
│   ├── utils/
│   │   ├── logger.py              # Structured JSON logging
│   │   ├── api_gateway.py         # HTTP retry wrapper
│   │   └── dataset_manager.py     # KB indexer
│   ├── middleware/
│   │   └── __init__.py            # require_auth, optional_auth
│   ├── evaluation/
│   │   └── benchmark.py           # Per-user trace evaluator (233 lines)
│   └── tests/
│       └── test_api.py            # 19 tests (188 lines)
├── frontend/
│   ├── package.json               # Dependencies & scripts
│   ├── next.config.ts             # Static export config
│   ├── components.json            # shadcn/ui config
│   ├── postcss.config.mjs         # PostCSS + Tailwind
│   ├── eslint.config.mjs          # ESLint config
│   ├── tsconfig.json              # TypeScript strict mode
│   ├── .env.local                 # Firebase client keys
│   └── src/
│       ├── app/
│       │   ├── page.tsx           # Simulator (2357 lines)
│       │   ├── layout.tsx         # Root layout (39 lines)
│       │   ├── globals.css        # Full theme (343 lines)
│       │   ├── dashboard/page.tsx # Control Center (387 lines)
│       │   ├── analytics/page.tsx # System Analytics (517 lines)
│       │   ├── activity/page.tsx  # Activity Timeline (519 lines)
│       │   ├── history/page.tsx   # Conversation History (429 lines)
│       │   └── timeline/page.tsx  # Farm Timeline (452 lines)
│       ├── components/
│       │   ├── ui/                # 20+ shadcn/ui components
│       │   ├── auth-screen.tsx    # Login/signup (265 lines)
│       │   ├── client-layout.tsx  # Navbar + auth gate (282 lines)
│       │   ├── command-palette.tsx # ⌘K nav (146 lines)
│       │   ├── data-loader.tsx    # Loading/error/empty (122 lines)
│       │   ├── error-boundary.tsx # Error boundary (66 lines)
│       │   └── speak-button.tsx   # TTS controls (235 lines)
│       ├── hooks/
│       │   ├── use-speech-recognition.ts (222 lines)
│       │   └── use-text-to-speech.ts (351 lines)
│       └── lib/
│           ├── api.ts             # HTTP + SSE + circuit breaker (294 lines)
│           ├── auth-context.tsx   # Firebase auth provider (150 lines)
│           ├── firebase.ts        # Firebase singleton (36 lines)
│           └── utils.ts           # cn() utility (6 lines)
├── knowledge_base/
│   ├── crops.json                 # 8 crops (178 lines)
│   ├── diseases.json              # 15 diseases (302 lines)
│   ├── fertilizers.json           # 8 fertilizers (142 lines)
│   ├── government_schemes.json    # 10 schemes (230 lines)
│   ├── market_intelligence.json   # MSP/mandis (68 lines)
│   ├── pests.json                 # 6 pests (146 lines)
│   ├── soil_health.json           # 5 soil types (147 lines)
│   └── treatments.json            # 12 disease sets (464 lines)
├── docs/
│   ├── architecture.md            # Mermaid diagrams (105 lines)
│   ├── demo_script.md             # 5-min walkthrough (33 lines)
│   ├── prompt.md                  # Gemini system prompt (655 lines)
│   ├── schemas.md                 # Firestore schemas (76 lines)
│   └── detail of my project..md   # Full narrative description
├── deployment/                    # (empty — deployment via firebase.json)
├── scripts/                       # (empty)
├── tests/                         # (empty — tests in backend/tests/)
├── public/
│   └── logo(seed-ai).png
├── .env                           # Root env vars (41 lines)
├── mcp_server/
│   ├── server.py                  # MCP server (8 tools, 4 resources)
│   ├── kb_loader.py               # Knowledge base loader
│   ├── requirements.txt           # mcp>=1.0.0
│   └── __init__.py
├── .gitignore                     # 28 rules
├── firebase.json                  # Firebase hosting config
├── firestore.rules                # Security rules
├── firestore.indexes.json         # 6 composite indexes
├── .firebaserc                    # Default project alias
├── firebaserules.md               # Rules documentation (56 lines)
├── README.md                      # Project readme (43 lines)
├── overview of capstone project.md # Competition overview (87 lines)
├── writeup_kaggle.md              # Kaggle writeup template (40 lines)
└── project_info.md                # This document
```

---

## 17. Capstone Project Details

### 17.1 Track
**Agents for Good** / **Freestyle** — Agricultural decision support using multi-agent AI

### 17.2 Key Concepts Demonstrated

| Concept | Implementation |
|---------|---------------|
| Multi-agent system | 13 specialized agents + memory + translation, orchestrated by Gemini |
| Gemini Function Calling | 10 tool declarations for dynamic agent selection |
| Tool Use | 4 external APIs (OpenWeatherMap, Data.gov.in, Google Gemini, HuggingFace) |
| Memory/Persistence | Firestore (5 collections), EventBus (batched async writes), DLQ |
| Decision Fusion | LLM-based FusionResult + local fallback fusion |
| Reflection | Gemini self-critique for safety and consistency |
| Guardrails | Rain-check (postpone spray >60% rain), budget-ceiling (warn >110%) |
| Graceful Degradation | Critical vs non-critical agent tiers, credential-optional features |
| Real-time Streaming | SSE with auth headers for live execution transparency |
| Zero Friction UX | Auto-inference of location/crop/budget from text, memory, or geolocation |
| Rate Limiting | Token-bucket, multi-key pool, 30s cooldown, g4f fallback |
| Multi-User Isolation | Auth, Firestore rules, per-user evaluator, Bearer tokens |
| Hybdrid Vision | YOLO11 + Gemma-4 + Gemini Vision + Qwen2.5-VL + HuggingFace models |
| Prompt Safety | 5-pattern injection sanitization in BaseAgent |
| Caching | 300s TTL md5-based result cache, Firestore memory cache with TTL |
| TTS | 12-language edge-tts with file caching + browser fallback |
| Speech Recognition | 11-language Web Speech API with auto-detect |
| MCP Server | 8 knowledge base tools + 4 resources via Model Context Protocol (`mcp_server/`) |

### 17.3 Evaluation Criteria Coverage
- **Problem Definition**: Agricultural decision-making fragmentation (7 challenges identified)
- **Solution Design**: Multi-agent AI orchestration with 5 execution modes
- **Implementation Quality**: 30+ Python modules, 15 agents, 6 frontend pages, production patterns
- **Agent Technology**: Function Calling, SSE streaming, structured output, reflection, guardrails, caching, MCP standard protocol
- **Documentation**: README, architecture diagrams (Mermaid), demo script, API docs, schemas, project info, competition overview, Kaggle writeup template

---

## 18. Responsible AI

SEED AI follows responsible AI principles:
- **Confidence scores** displayed for all recommendations (High/Medium/Low)
- **Explanations** provided for every decision (reasoning field in all AgentResults)
- **Tool outputs** cited where feasible (evidence_sources in FusionResult)
- **Unsupported claims** avoided
- **Expert consultation** encouraged for severe conditions
- **User privacy** protected with Firebase Authentication and consent-based data storage
- **Safety** prioritized over completeness in all recommendations (guardrails prevent unsafe spray timing)
- **Reflection** self-checks for contradictions and safety issues

---

## 19. Summary Statistics

| Metric | Value |
|--------|-------|
| Total backend Python files | 30 |
| Total frontend TypeScript/TSX files | 45+ |
| Total lines of code (est.) | ~15,000+ |
| Agent count | 15 (13 specialized + memory + translation) |
| Registered API endpoints | 22+ |
| External API integrations | 8 (Gemini, OpenRouter, HuggingFace, OpenWeatherMap, Data.gov.in, Firebase, Supabase, edge-tts) |
| Knowledge base entries | 8 files, ~1,877 lines |
| Gemini API keys supported | Up to 11 (round-robin) |
| Languages (speech/TTS) | 11 / 12 |
| Frontend pages | 6 |
| shadcn/ui components | 20+ |
| SSO providers | 3 (anonymous, email/password, Google) |
| Vision models | 5 (YOLO11, Gemma-4, Gemini Vision, Qwen2.5-VL, HuggingFace ViT/MobileNetV2/SigLIP2) |
| Firestore collections | 5 (farm_memory, conversation_history, disease_history, execution_logs, dlq_events) |

---

*Built for the Google AI Agents: Intensive Vibe Coding Capstone Project — July 2026*

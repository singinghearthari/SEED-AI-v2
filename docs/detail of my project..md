# SEED AI
## Smart Ecosystem for Enhanced Agricultural Decisions
### An Autonomous Agricultural Intelligence System Powered by AI Agents

**Google AI Agents: Intensive Vibe Coding Capstone Project — July 2026**

---

## Executive Summary

Agriculture is becoming increasingly data-driven, yet many farmers still rely on fragmented information from multiple applications. Weather forecasts, disease detection tools, market price platforms, and government scheme portals operate independently, forcing farmers to manually interpret and combine information before making critical decisions.

SEED AI addresses this challenge by introducing an Autonomous Agricultural Intelligence System built on a Multi-Agent AI Architecture. Instead of functioning as a chatbot that simply answers questions, SEED AI orchestrates multiple specialized AI agents that collaborate to analyze crop conditions, retrieve real-time information, reason over multiple data sources, generate actionable farming plans, and continuously adapt recommendations based on new observations and historical farm data. The platform demonstrates how autonomous AI agents can transform agriculture from reactive decision-making into proactive, personalized farm management.

---

## Problem Statement

Farmers frequently encounter several interconnected challenges:

1. **Delayed identification of crop diseases** — Most farmers cannot access expert diagnostics quickly; visual symptoms are often misinterpreted
2. **Unpredictable weather affecting crop health** — Rain, temperature swings, and humidity directly impact disease spread and treatment efficacy
3. **Limited access to personalized agricultural guidance** — Generic advice does not account for the farmer's specific crop, location, soil, and budget
4. **Fragmented information across multiple platforms** — No single tool provides weather, disease diagnosis, market prices, government schemes, and task planning in one place
5. **Difficulty selecting treatments within budget** — Farmers must weigh treatment effectiveness against cost without clear tradeoff analysis
6. **Lack of continuous monitoring and follow-up** — Without persistent memory, each query starts from scratch, ignoring farm history
7. **Limited awareness of government subsidies and support schemes** — Many eligible farmers miss out on PMFBY, PM-KISAN, KCC, and other schemes due to lack of information

Existing digital solutions typically address only one problem at a time, leaving farmers responsible for combining diverse information sources into a coherent decision.

---

## Proposed Solution

SEED AI introduces an autonomous multi-agent ecosystem where specialized AI agents collaborate to generate personalized farming decisions. Rather than simply answering questions, the system:

- **Observes** — Accepts text, voice (Web Speech API, 11 languages with auto-detect), and image inputs (drag-and-drop, camera capture)
- **Reasons** — Uses Google Gemini Function Calling to dynamically determine which agents and tools are needed
- **Plans** — Generates 7-day action schedules with task priorities (Critical, High, Medium, Low)
- **Calls external tools** — Integrates with OpenWeatherMap (live weather), Data.gov.in Agmarknet (market prices), HuggingFace Inference API (vision models), Firebase Firestore (memory), Supabase Storage (images)
- **Coordinates multiple AI agents** — Up to 13 specialized agents + memory + translation running concurrently with staggered execution (Tier 1 core → fusion → Tier 2 enrichment)
- **Generates action plans** — Fuses outputs from all agents into a single structured FusionResult with evidence sources, confidence scores, risk levels, and alternatives considered
- **Learns from historical farm data** — Firestore memory across sessions with farm profile, disease history, conversation history, and execution traces
- **Reflects on decisions** — Gemini self-critique for safety, budget compliance, spray timing, and contradiction detection
- **Applies guardrails** — Rain check (automatically delays chemical sprays if rain probability > 60%), budget ceiling (warns and suggests low-cost alternatives if total cost > 110% of budget)
- **Streams real-time execution** — Server-Sent Events (SSE) with auth headers show every agent step, latency, tools used, and status to the frontend in a macOS-style terminal
- **Supports failover gracefully** — Multi-key Gemini pool (up to 11 keys, round-robin), g4f GPT-4o fallback when Gemini exhausted, tiered agent criticality (non-critical agents can fail without blocking results), credential-optional feature degradation

---

## Vision

Farmers don't need more information — they need timely, personalized decisions.

SEED AI transforms agricultural decision-making by orchestrating specialized AI agents that analyze crop conditions, retrieve real-time environmental data, optimize treatment strategies, and provide adaptive recommendations tailored to each farmer's context.

---

## Objectives

1. **Develop an autonomous AI agent ecosystem for agriculture** — 15 agents covering analysis, prediction, planning, persistence, and communication
2. **Demonstrate intelligent multi-agent collaboration** — Dynamic routing, concurrent Tier 1 execution, staggered Tier 2 enrichment
3. **Enable real-time reasoning using multiple external tools** — 8 external API integrations with automatic failover
4. **Deliver personalized farming recommendations** — Zero-friction context inference (text patterns, memory, geolocation)
5. **Improve accessibility through multilingual interaction** — 11-language speech recognition, 12-language TTS (edge-tts + browser fallback), bilingual translation (Tamil/English)
6. **Promote responsible and trustworthy AI** — Confidence scores, explanations, reflection, guardrails, injection sanitization, privacy protection

---

## Why AI Agents?

Traditional AI applications respond to individual user prompts. SEED AI moves beyond conversational AI by introducing autonomous decision-making through specialized agents. Each agent performs a dedicated task while an orchestrator coordinates the overall workflow, ensuring that recommendations are context-aware, data-driven, and dynamically generated. The orchestrator uses Gemini Function Calling with 10 declared tool functions, resolves routing both deterministically (keyword matching, execution mode) and via LLM (auto mode), applies guardrails after fusion, reflects on the final decision, and persists everything to Firestore via an async EventBus.

---

## Core Capabilities

### 1. Crop Disease Diagnosis (Hybrid Vision Pipeline)
- **YOLO11** (local, yolo11n.pt, CUDA/MPS/CPU auto-detect) — detects 17 disease classes + 10 waste classes with bounding boxes and annotated images
- **OpenRouter Gemma-4 26B** (primary vision LLM) — structured JSON disease analysis
- **Gemini Vision 2.0 Flash** (fallback when OpenRouter fails) — multimodal content analysis
- **Qwen2.5-VL-7B-Instruct** (via HuggingFace Inference API) — expert analysis with latency tracking
- **HuggingFace serverless models**: ViT (crop_leaf_diseases_vit), MobileNetV2 (plant-disease-mobilenetv2), SigLIP2 (waste classifier)
- **Outputs**: disease name, severity (Mild/Moderate/Severe), confidence (%), affected area (%), visual explanation, immediate action

### 2. Weather Intelligence
- Real-time weather retrieval via OpenWeatherMap API
- Agricultural risk assessment via Gemini structured schema
- **WeatherRiskAssessment**: rain_probability, humidity, temperature, wind_speed, weather_risk (Low/Moderate/High/Critical), spray_safe (bool), irrigation_needed (bool), reasoning
- Live data confidence: 85%, fallback (Gemini general knowledge): 50%

### 3. Budget-Aware Planning
- Treatment cost estimation with cheapest vs best-value comparison
- Budget compliance check (warns if total > 110% of budget)
- Alternative low-cost recommendations
- **TreatmentOption**: name (e.g., Mancozeb 75% WP), type (Chemical/Organic/Biological/Cultural), dosage, application, cost_estimate_inr (₹280), effectiveness (High/Medium/Low)
- **BudgetPlan**: cheapest_option, best_value_option, budget_limit, estimated_total_cost, budget_compliant, savings_tip, reasoning
- Knowledge base: 40+ treatments across 12 diseases, 8 fertilizers with prices

### 4. Market Intelligence
- Live prices from Data.gov.in Agmarknet API (20,000+ records indexed)
- MSP data for 26 crops (Kharif: 17, Rabi: 6, Other: 3) with cost of production
- 8 major APMC mandis tracked (Azadpur Delhi, Vashi Mumbai, Lasalgaon Nashik, etc.)
- Price volatility index (Tomato: Very High 5x, Onion: Very High 10x, Potato: High 3x, Wheat/Rice: Low MSP-supported)
- **MarketAnalysis**: crop, current_price_per_kg, price_trend (Rising/Stable/Falling), sell_recommendation, optimal_timing, reasoning

### 5. Government Assistance
- 10 schemes catalogued: PMFBY (crop insurance, ₹15,500 Cr budget), PM-KISAN (₹6,000/yr income support), KCC (4% interest credit), Soil Health Card (free testing), PMKSY (55% irrigation subsidy), e-NAM (1,361 mandis), PM Kisan Maandhan (₹3,000/month pension), AIF (₹1 Lakh Cr infrastructure fund), PKVY (organic farming subsidy), SMAM (equipment subsidy)
- **GovernmentSchemeResult**: eligible_schemes[], scheme_details (name, type, benefits, eligibility, premium, budget, website, helpline), application_guidance, reasoning

### 6. Intelligent Task Scheduling
- Automatically creates personalized 7-day farming schedule with priorities
- **FarmTask**: day (e.g., "Tomorrow", "Wednesday"), task ("Spray fungicide"), reason ("Early Blight treatment — copper-based fungicide recommended"), expected_outcome ("Disease progression halted"), priority ("High")
- Check-off tracking with animated progress bar on the Timeline page

### 7. Farm Memory (Persistent)
- Firestore collections: farm_memory, conversation_history, disease_history, execution_logs, dlq_events
- MemoryAgent actions: retrieve, update, log_conversation, log_execution, log_disease, get_history, get_traces, batch_persist, dlq_retry
- Cache with TTL (30s traces, 120s history), cache invalidation by prefix
- Schema version: 2
- Dead Letter Queue for failed batch persists (max 3 retries)

### 8. Multilingual Interaction
- Speech recognition: 11 Indian languages with auto-detect mode (hi-IN → en-IN → ta-IN → ...)
- Text-to-Speech: 12 languages (backend edge-tts), 10 languages (browser), 29 voices
- Language detection via Unicode script analysis
- Translation Agent: bilingual (Tamil ↔ English), fixed confidence 90%

### 9. Soil & Nutrient Analysis
- 5 soil types: Alluvial (43% coverage), Black/Vertisol (24%), Red/Alfisol (18%), Laterite (8%), Saline-Sodic (3%)
- Physical characteristics: texture, pH (6.5–8.0 range), organic carbon, water retention, drainage
- Nutrient status: N, P, K, Zn (48% deficient in alluvial), Fe, Ca/Mg
- **SoilNutrientResult**: soil_ph, nitrogen_level, phosphorus_level, potassium_level, organic_carbon_percent, nutrient_deficiencies[], fertilizer_recommendations[], soil_health_score (0–100), soil_type_match, reasoning

### 10. Pest Management (Entomologist)
- 6 pests: Whitefly (Bemisia tabaci), Helicoverpa armigera, Brown Plant Hopper, Fall Armyworm, Aphids, Pink Bollworm
- Management strategies: cultural (yellow sticky traps, border crops), biological (Encarsia formosa, Beauveria bassiana), chemical (Spiromesifen, Diafenthiuron), organic (neem oil 5%)
- Economic threshold levels, life cycle, peak season, regional distribution

### 11. Irrigation Management
- 7-day irrigation schedule based on weather and crop water requirements
- Methods: drip, sprinkler, flood with recommendations
- **IrrigationResult**: irrigation_schedule_7day[], recommended_irrigation_method, water_requirement_liters_per_acre_daily, moisture_conservation_tips, system_maintenance_protocols, reasoning

### 12. Waste-to-Wealth
- Revenue opportunities from agricultural waste: compost, biochar, biofuel, animal feed
- Optional waste image classification via HuggingFace SigLIP2
- **WasteToWealthResult**: waste_streams[], opportunities[], total_potential_revenue, equipment_needed, government_subsidies, environmental_benefits, quick_wins[], reasoning

### 13. Crop Prediction
- Optimal crop selection based on location, season, soil type, and budget
- 8 crops in knowledge base: Tomato, Rice, Wheat, Cotton, Potato, Onion, Mango, Sugarcane
- **CropPredictionResult**: top_recommendations[], seasonal_analysis, soil_suitability_notes, market_demand_forecast, risk_factors[], reasoning

### 14. Disease Prediction (Preventive)
- Predicts diseases before symptoms appear based on weather + crop + season + regional history
- **DiseasePredictionResult**: predicted_diseases[] with probability %, overall_risk_level, environmental_risk_factors[], monitoring_schedule[], reasoning

### 15. MCP Server (Model Context Protocol)
- Standalone MCP server at `mcp_server/` exposing 8 knowledge base tools via the MCP standard
- **8 tools**: get_disease_info, get_treatment_plan, get_crop_guide, find_government_schemes, get_pest_management, get_soil_guide, get_market_prices, knowledge_base_categories
- **4 resources**: seedai://diseases/list, seedai://crops/list, seedai://schemes/list, seedai://pests/list
- Transport modes: stdio (CLI) or SSE (HTTP)
- Any MCP-compatible client can discover and call these tools for agricultural data
- Implementation: `mcp` Python SDK (FastMCP), <150 lines of server code

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FARMER                                       │
│            ┌──────────┼──────────┐                                  │
│            ▼          ▼          ▼                                  │
│          Voice      Image      Text                                 │
│     (Web Speech)  (Upload)   (Query)                               │
└────────────────────────┬────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────────┐
│                  FRONTEND (Next.js 16 + Tailwind 4)                  │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐  ┌────────┐  │
│  │Simulator │  │Dashboard │  │Activity│  │Analytics │  │History │  │
│  │ 2357 ln  │  │ 387 ln   │  │ 519 ln │  │ 517 ln  │  │ 429 ln │  │
│  └──────────┘  └──────────┘  └────────┘  └──────────┘  └────────┘  │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ SSE Client (ReadableStream + circuit breaker + auth)     │      │
│  │ SpeechRecognition (11 lang auto-detect)                  │      │
│  │ TTS (backend edge-tts + browser fallback)                │      │
│  │ Geolocation (Nominatim reverse geocoding)                │      │
│  │ shadcn/ui + Framer Motion + Recharts + Lucide            │      │
│  └──────────────────────────────────────────────────────────┘      │
└────────────────────────┬────────────────────────────────────────────┘
                         │ SSE / REST (Firebase Auth Bearer Token)
┌────────────────────────▼────────────────────────────────────────────┐
│                   BACKEND (FastAPI + Python 3.10+)                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │             GEMINI ORCHESTRATOR AGENT (1195 lines)           │   │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐          │   │
│  │  │Routing  │ │Tier 1    │ │Fusion   │ │Guardrails│          │   │
│  │  │Engine   │ │Execution │ │Engine   │ │+Reflect  │          │   │
│  │  └─────────┘ └──────────┘ └─────────┘ └──────────┘          │   │
│  │  ┌─────────┐ ┌──────────┐ ┌─────────┐ ┌──────────┐          │   │
│  │  │Cache    │ │Tier 2    │ │EventBus │ │Evaluator │          │   │
│  │  │(300s)   │ │Fire-n-   │ │Persist  │ │Traces    │          │   │
│  │  │         │ │forget    │ │         │ │          │          │   │
│  │  └─────────┘ └──────────┘ └─────────┘ └──────────┘          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  AGENTS (13 + memory + translation):                                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Vision   │ │ Weather  │ │ Crop     │ │ Soil &   │ │ Entomol. │  │
│  │ (Hybrid  │ │(OWM +    │ │Knowledge │ │ Nutrient │ │ (6 pests)│  │
│  │ pipeline)│ │Gemini)   │ │(RAG+KB)  │ │(5 soils) │ │          │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Market   │ │Budget    │ │Government│ │Task      │ │Irrigation│  │
│  │(Agmarknet│ │(40+      │ │Scheme    │ │Planning  │ │(7-day    │  │
│  │+Gemini)  │ │treatments│ │(10schms) │ │(7-day)   │ │schedule) │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Crop Pred.│ │Disease   │ │Waste-to- │ │Memory    │ │Translate │  │
│  │(8 crops) │ │Prediction│ │Wealth    │ │(Firestore│ │(Ta/En)   │  │
│  │          │ │(Prevent.)│ │(SigLIP2) │ │+DLQ)     │ │          │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                                                                      │
│  SERVICES:                                                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Gemini   │ │Firebase  │ │Supabase  │ │EventBus  │ │TTS       │  │
│  │(11 keys, │ │Auth+FS   │ │Storage   │ │+PHandler │ │edge-tts  │  │
│  │rate-limit│ │+verify   │ │images    │ │+DLQ      │ │12 langs  │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                  │
│  │YOLO11(yolo11n│ │OpenRouter    │ │Qwen2.5-VL    │                  │
│  │.pt, 17+10cls)│ │Gemma-4 26B   │ │HF Inference  │                  │
│  └──────────────┘ └──────────────┘ └──────────────┘                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐│
│  │HF Analyzer   │ │Weather Svc   │ │Market Svc    │ │MCP Server    ││
│  │ViT+MobileNet │ │OpenWeatherMap│ │Data.gov.in   │ │8 KB tools    ││
│  │+SigLIP2      │ │              │ │Agmarknet     │ │seedai:// URIs││
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘│
└────────────────────────┬────────────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────────────┐
│                  EXTERNAL SERVICES                                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ Google   │ │Hugging   │ │OpenRouter│ │Open-     │ │Data.gov  │  │
│  │ Gemini   │ │Face      │ │Gemma-4   │ │WeatherMap│ │.in       │  │
│  │(11 keys) │ │Inference │ │(free)    │ │          │ │Agmarknet │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│  ┌──────────────┐ ┌──────────────────┐ ┌──────────────────┐         │
│  │Firebase      │ │Supabase Storage  │ │g4f (GPT-4o      │         │
│  │Firestore+Auth│ │(leaf-images      │ │Gemini fallback)  │         │
│  │              │ │bucket)           │ │                  │         │
│  └──────────────┘ └──────────────────┘ └──────────────────┘         │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Execution Modes

| Mode | Description | Agents Used | Use Case |
|------|-------------|-------------|----------|
| **Auto** | AI-determined routing (default) | Tier 1 core + market + LLM-chosen specialists | General queries |
| **Fast Track** | Quick disease diagnosis | vision, disease_prediction | Urgent leaf disease ID |
| **Ensemble** | 5-agent coordinated swarm | soil_nutrient, weather, crop_knowledge, disease_prediction, market | Comprehensive crop health check |
| **Specific** | Single designated specialist | User-selected agent | Targeted expert question |
| **All (Swarm)** | Full end-to-end simulation | All 13 agents | Complete farm assessment |

---

## Example Scenario

**Farmer Input:**
- Query: "I have three acres of tomatoes. Budget ₹4000. Rain expected tomorrow."
- Image: Diseased tomato leaf (uploaded via drag-and-drop)
- The system auto-infers: Location = Bangalore (from geolocation or memory), Crop = Tomato, Budget = ₹4000

**System Response (Autonomous Agent Pipeline):**

1. **Vision Agent** → Detects **Early Blight** (Alternaria solani) with 94% confidence, Moderate severity (30% affected area), immediate action: apply fungicide
2. **Weather Agent** → Rain probability 70% tomorrow, 28°C, 85% humidity — favorable for fungal spread
3. **Crop Knowledge Agent** → Early Blight treatment protocols: chlorothalonil (₹450), mancozeb (₹280), azoxystrobin (₹800), copper oxychloride (₹300), Trichoderma viride biological (₹200), crop rotation (₹0)
4. **Budget Agent** → Mancozeb ₹280 recommended (cheapest effective option), total cost ₹1,050 (well under ₹4,000 budget, ₹2,950 remaining)
5. **Market Agent** → Tomato prices currently ₹35/kg (stable), recommend waiting 2 weeks for harvest
6. **Government Scheme Agent** → Eligible: PMFBY crop insurance, PM-KISAN income support, KCC credit, Soil Health Card
7. **Task Planning Agent** → 7-day schedule: Day 1 spray mancozeb (after rain passes), Day 3 inspect, Day 5 irrigation, Day 7 follow-up image
8. **Guardrails** → Rain probability 70% > 60% → delays chemical spray to Day 2
9. **Fusion** → Combined into one actionable plan with 88% confidence (High)
10. **Memory** → Saves disease event, treatment, budget usage, farm profile update
11. **SSE Stream** → Frontend shows each step in real-time with agent latencies

---

## Multi-Agent Workflow (Detailed)

### Step 1: Request Intake
- User submits text query (typed or voice), optionally with crop leaf image
- Frontend validates inputs, converts speech to text (auto-detect language)
- Image validated for MIME type (JPEG/PNG/WebP/GIF) and size (max 10MB)

### Step 2: Orchestrator Analysis
- Cache check (md5 hash, 300s TTL, skipped for images)
- Memory retrieval from Firestore (farm profile, disease history)
- Context inference (fill missing location/crop/budget from text patterns, memory, or geolocation)
- Gemini Function Calling determines relevant agents
- Execution mode determines routing strategy

### Step 3: Agent Execution
- **Tier 1 (Concurrent)**: crop_knowledge, weather, soil_nutrient, budget, market (always) + LLM-resolved specialists run via `asyncio.gather` with 60s timeout and 2 retry attempts
- Decision Fusion Engine combines all outputs via Gemini structured output (LLMFusionSchema), falls back to local non-LLM fusion
- Guardrails applied (rain check, budget ceiling)
- Reflection via Gemini self-critique
- **Tier 2 (Fire-and-forget)**: government_schemes, waste_to_wealth, task_planning run in background via `asyncio.ensure_future`

### Step 4: Result Generation
- EventBus batched persistence to Firestore (2s flush or 50 events)
- Evaluation trace stored with per-user isolation
- SSE result streamed to frontend
- Frontend displays: swarm visualization, event log, 6 result tabs (Action Plan, Timeline, Weather & Irrigation, Soil & Health, Markets & Schemes, Waste Utilization)

---

## Technology Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| Next.js | 16.2.9 | Framework (App Router, static export) |
| TypeScript | 5.x | Type safety (strict mode) |
| Tailwind CSS | 4.x | Styling (base-nova) |
| Framer Motion | 12.42.0 | Animations |
| shadcn/ui | Latest | UI components (20+) |
| Recharts | 3.9.1 | Charts (pie, bar, line) |
| Lucide React | 1.21.0 | Icons |
| Firebase Client | 12.15.0 | Authentication |
| @base-ui/react | 1.6.0 | Headless UI primitives |
| tw-animate-css | 1.4.0 | Animation utilities |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.115+ | Web framework |
| Python | 3.10+ | Runtime |
| google-genai | 1.0+ | Gemini SDK |
| firebase-admin | 6.0+ | Firebase Admin SDK |
| supabase | 2.0+ | Supabase Storage |
| edge-tts | 6.0+ | Text-to-Speech |
| httpx | 0.27+ | HTTP client |
| tenacity | 8.0+ | Retry logic |
| ultralytics | 8.3+ | YOLO11 |
| huggingface_hub | 0.27+ | HuggingFace Inference |
| Pillow | 10+ | Image processing |
| g4f | 0.4+ | Gemini fallback (GPT-4o) |
| pandas | 2.0+ | Data processing |
| **mcp** | **1.28+** | **MCP SDK — Model Context Protocol server** |
| pytest | 8.0+ | Testing |
| pytest-asyncio | 0.24+ | Async testing |

### AI & ML Models
| Model | Provider | Purpose |
|-------|----------|---------|
| gemini-2.5-flash | Google Gemini | Primary LLM (orchestration, all agents) |
| gemma-4-26b-a4b-it | OpenRouter (free) | Primary vision analysis |
| gemini-2.0-flash | Google Gemini | Vision fallback |
| Qwen2.5-VL-7B-Instruct | HuggingFace | Expert vision analysis |
| YOLO11n | Ultralytics (local) | Object detection (17 disease + 10 waste classes) |
| crop_leaf_diseases_vit | HuggingFace (ViT) | Plant disease classification |
| plant-disease-mobilenetv2 | HuggingFace | Plant disease classification |
| Augmented-Waste-Classifier-SigLIP2 | HuggingFace | Waste classification |
| GPT-4o (g4f) | Free tier | Gemini fallback LLM |

### MCP Server (Model Context Protocol)
| Tool | Purpose | KB Source |
|------|---------|-----------|
| `get_disease_info` | Search diseases by name or affected crop | diseases.json |
| `get_treatment_plan` | Get treatment options for a disease | treatments.json |
| `get_crop_guide` | Full agronomic guide per crop | crops.json |
| `find_government_schemes` | Find eligible government schemes | government_schemes.json |
| `get_pest_management` | Pest ID + cultural/biological/chemical/organic controls | pests.json |
| `get_soil_guide` | Soil type info, pH, nutrients, management | soil_health.json |
| `get_market_prices` | MSP data for 26 Kharif/Rabi/Other crops | market_intelligence.json |
| `knowledge_base_categories` | List all 8 KB categories | All KB files |
| **Resources** | `seedai://diseases/list`, `crops/list`, `schemes/list`, `pests/list` | Static data |

**Run:** `python mcp_server/server.py --transport stdio` (or `--transport sse` for HTTP)

### External APIs
| API | Purpose | Key Optional? |
|-----|---------|---------------|
| OpenWeatherMap | Live weather data (rain, temp, humidity, wind) | Yes |
| Data.gov.in Agmarknet | Commodity market prices (20k+ records) | Yes |
| OpenRouter | Gemma-4 vision analysis (free tier) | Yes |
| HuggingFace Inference | Qwen2.5-VL, ViT, MobileNetV2, SigLIP2 | Yes |
| Gemini API (11 keys) | Primary LLM (rate-limited, multi-key) | **Required** |
| Firebase Auth + Firestore | Authentication, database, hosting | **Required** |
| Supabase Storage | Image uploads (leaf-images bucket) | Yes |
| edge-tts (local) | Text-to-Speech (no API key needed) | N/A |

### Database & Storage
| Service | Purpose | Collections/Buckets |
|---------|---------|---------------------|
| Firebase Firestore | Persistent memory, history, traces | farm_memory, conversation_history, disease_history, execution_logs, dlq_events |
| Supabase Storage | Image hosting | leaf-images bucket (1hr signed URLs) |
| Local JSON files | Knowledge base | 8 files (crops, diseases, treatments, fertilizers, pests, soil, schemes, market) |

### Authentication
| Method | Implementation |
|--------|---------------|
| Anonymous | Firebase Auth (auto sign-in) |
| Email/Password | Firebase Auth (login + register forms) |
| Google OAuth | Firebase signInWithPopup |
| Token Refresh | 50-minute background interval |
| Backend Verification | Firebase Admin SDK verify_token_cached (SHA-256, 5-min TTL, 100-entry cache) |

---

## Multi-Agent Workflow Diagram

```
Step 1: User Input
┌──────────────────────────────────────────────────┐
│  Text Query (keyboard or voice→speech→text)      │
│  + Optional Leaf Image (drag-drop or click)      │
│  + Optional Location/Crop/Budget (auto-inferred) │
└──────────────────────┬───────────────────────────┘
                       │
Step 2: Orchestrator
┌──────────────────────▼───────────────────────────┐
│  Cache Check (md5 hash, 300s TTL)                │
│  Memory Load (Firestore → farm profile)          │
│  Context Inference (text/memory/geolocation)      │
│  Gemini Function Calling → Dynamic Agent Routing  │
│  Execution Mode: Auto / Fast / Ensemble / Specific│
│                                                   │
│  Tier 1 Agents (Concurrent asyncio.gather, 60s): │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │crop_     │ │weather   │ │soil_     │          │
│  │knowledge │ │          │ │nutrient  │          │
│  └──────────┘ └──────────┘ └──────────┘          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │budget    │ │market    │ │[LLM-    │          │
│  │          │ │(always)  │ │ chosen] │          │
│  └──────────┘ └──────────┘ └──────────┘          │
└──────────────────────┬───────────────────────────┘
                       │
Step 3: Fusion & Reflection
┌──────────────────────▼───────────────────────────┐
│  Decision Fusion (Gemini LLMFusionSchema)         │
│  └→ Fallback: _local_fusion() if LLM fails       │
│                                                   │
│  Guardrails:                                      │
│  ├─ Rain Check: rain>60% → postpone sprays       │
│  └─ Budget Ceiling: cost>110% → warn+alternatives│
│                                                   │
│  Reflection (Gemini self-critique):               │
│  ├─ Budget compliance check                       │
│  ├─ Spray safety vs rain                          │
│  └─ Contradiction detection                       │
│                                                   │
│  Tier 2 Agents (Fire-and-forget):                 │
│  ├─ government_schemes                            │
│  ├─ waste_to_wealth                               │
│  └─ task_planning (7-day schedule)                │
└──────────────────────┬───────────────────────────┘
                       │
Step 4: Output
┌──────────────────────▼───────────────────────────┐
│  EventBus → Batch Firestore Persist               │
│  ├─ farm_memory (upsert)                          │
│  ├─ conversation_history (new doc)                │
│  ├─ execution_logs (new doc)                      │
│  └─ disease_history (new doc, conditional)        │
│                                                   │
│  AgentEvaluator → Per-user trace + JSON log      │
│  SSE Stream → Frontend (events→pre_result→result) │
└──────────────────────────────────────────────────┘
```

---

## SSE Event Types

| Type | Phase | Data |
|------|-------|------|
| `event` | Running | `{ agent, message, latency_ms, tools_used, status: "running"/"completed"/"failed", timestamp }` |
| `pre_result` | Fusion ready | `{ message: "Tier-1 fusion ready..." }` |
| `result` | Complete | `{ summary, recommended_actions, confidence, agent_results, agent_results_meta, execution_metadata }` |
| `error` | Error | `{ message, degraded_result }` |

---

## User Experience

The interface transparently visualizes the reasoning process:

```
┌─ SEED AI Command Center ───────────────────────────────────┐
│  [Mic] [Upload Image] [Query Input] [Run →]                 │
│  Mode: [Auto▼]  Agent: [Any▼]                               │
│  Presets: [Tomato Blight] [Rice Irrigation] [Budget...]     │
├────────────────────────────────────────────────────────────┤
│  ┌─ Swarm Visualization ──┐  ┌─ Event Log ───────────────┐ │
│  │  ○──○──○──○──○         │  │ ● ● ●  [Search...]      │ │
│  │  │  │  │  │  │         │  │ ✓ Vision Agent   1.2s    │ │
│  │  ○──○──○──○──○         │  │ ⏳ Weather Agent 0.8s    │ │
│  │  │  │  │  │  │         │  │ ✓ Crop K. Agent  1.5s    │ │
│  │  ○──○──○──○──○         │  │ ⏳ Budget Agent   0.6s    │ │
│  │                        │  │ ✓ Market Agent   1.1s    │ │
│  └────────────────────────┘  └──────────────────────────┘ │
│  ┌─ Results ────────────────────────────────────────────┐ │
│  │  [Action Plan] [Timeline] [Weather] [Soil] [Market]  │ │
│  │                                                        │ │
│  │  Disease: Early Blight (94% confidence)                │ │
│  │  Severity: Moderate (30% affected)                     │ │
│  │  Treatment: Mancozeb 75% WP — ₹280 (budget: ₹4,000)  │ │
│  │  ⚠ Rain alert: 70% — postpone spray to Day 2         │ │
│  │                                                        │ │
│  │  7-Day Schedule:                                       │ │
│  │  ☐ Day 1: Inspect field + prepare spray               │ │
│  │  ☐ Day 2: Apply Mancozeb (morning, no rain)           │ │
│  │  ☐ Day 3: Monitor for improvement                     │ │
│  │  ☐ Day 5: Irrigation (drip, morning)                  │ │
│  │  ☐ Day 7: Upload follow-up image                      │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

This improves transparency and user trust by showing exactly what the AI is doing at every step.

---

## Security & Multi-User Data Isolation

SEED AI implements production-grade tenant isolation to ensure every authenticated user can access only their own data:

### Authentication
- Firebase Authentication with anonymous, email/password, and Google OAuth sign-in
- Automatic token refresh via Firebase SDK (50-minute background interval)
- Auth state persisted across browser sessions with `onAuthStateChanged`

### Backend Authorization
- `require_auth` FastAPI dependency extracts and verifies Firebase ID tokens from `Authorization: Bearer` headers — if Firebase is unavailable, falls back to synthetic anonymous UID
- Every data endpoint enforces user_id matching between the token's UID and the requested resource
- Orchestration endpoints (`/orchestrate`, `/orchestrate/upload`) verify and override client-provided `user_id` with the authenticated UID
- `optional_auth` available for endpoints that work with or without authentication

### Frontend Security
- `auth-context.tsx` provides `getAuthToken()` for automatic token injection with 50-minute background refresh
- `fetchJSONWithAuth` attaches bearer tokens to authenticated API calls
- `createSSEStreamWithAuth` injects auth headers into SSE connections — replaces `EventSource` (which lacks header support) with fetch-based ReadableStream
- No hardcoded user IDs in source code — all requests use the authenticated UID
- SSE streams read auth tokens from request headers (never query params, avoiding URL exposure)

### In-Memory Isolation
- `AgentEvaluator.trace_data` converted from shared global list to per-user dictionary (`Dict[str, list]`)
- All evaluator methods (`start_trace`, `end_trace`, `get_user_traces`, `get_user_summary_stats`, `generate_downloadable_report`) scoped to a specific user
- Traces also appended to JSON log file (`logs/evaluation_report.json`) with user_id embedded

### Firestore Security Rules
Strict tenant isolation in `firestore.rules`:
- `farm_memory/{userId}`: access only when `request.auth.uid == userId`
- `conversation_history/{docId}`: create/read/update/delete only when `resource.data.user_id == request.auth.uid`
- `execution_logs/{docId}`: same pattern
- `disease_history/{docId}`: same pattern
- Default deny for all unlisted collections

### Frontend API Circuit Breaker
- Circuit breaker with 4 failover URLs (localhost:8000, 127.0.0.1:8000, localhost:8001, etc.)
- `FAILURE_THRESHOLD = 3` — opens circuit after 3 consecutive failures per URL
- `COOLDOWN_MS = 30000` — 30s cooldown before retrying a failed URL
- Retry on 429 (rate limit) and 5xx (server error) status codes

---

## Performance & Caching

### Backend Caching
- **Orchestrator result cache**: md5 hash of query context, 300s TTL, max 100 entries (skipped for image queries)
- **MemoryAgent cache**: In-memory cache with TTL (30s for traces, 120s for history), prefix-based invalidation
- **Token verification cache**: SHA-256 hash key, 5-minute TTL, max 100 entries, oldest-eviction
- **TTS audio cache**: SHA-256 key, local file storage, cache cleanup by max age

### Frontend Performance
- `React.memo` on 5 components (AgentNode, ProgressIndicator, EventLog, ReportActions, PerformanceMetrics)
- `useMemo` for derived data (active agents, agent status map, filtered events, counts)
- `useCallback` for event handlers, auto-inference, voice input
- Refs for all form values (avoids stale closures in async SSE callbacks)
- Throttled event flusher (50ms debounce between React state updates)
- 180s timeout with AbortController for orchestration requests
- Optimized package imports for lucide-react, recharts, framer-motion

---

## Responsible AI

SEED AI follows responsible AI principles:

- **Confidence scores** displayed for all recommendations (High: 90-100%, Medium: 75-89%, Low: <75%)
- **Explanations** provided for every decision (reasoning field in all AgentResults, per-agent reasoning in FusionResult)
- **Tool outputs** cited where feasible (evidence_sources in FusionResult links to specific data)
- **Unsupported claims** avoided (no hallucinated statistics)
- **Expert consultation** encouraged for severe conditions
- **User privacy** protected with Firebase Authentication — all data stored with user_id ownership enforced at database, backend, and frontend layers
- **Safety** prioritized over completeness (guardrails prevent unsafe spray timing, reflection checks for contradictions)
- **Confidence labeling**: `confidence_to_label()` maps 0–100 score to High/Medium/Low
- **Reflection modifies outputs**: if Gemini finds safety issues in fusion result, it revises the recommendation
- **Prompt injection protection**: BaseAgent sanitizes 5 injection patterns across all agents
- **No secrets in code**: `.gitignore` blocks `.env`, `*-adminsdk-*.json`, `serviceAccountKey*.json`, `logs/`

---

## Expected Impact

| Metric | Target |
|--------|--------|
| Disease Analysis Time | <10 seconds |
| Personalized Plan Generation | <15 seconds |
| Supported Languages (Speech/TTS) | 11 / 12 |
| External Tool Calls | 6–10 per query |
| Farm Memory | Persistent (Firestore, schema v2) |
| AI Planning | Multi-Agent (15 agents) |
| User Interaction | Voice, Image, Text |
| Concurrent Agent Execution | Up to 8 Tier 1 agents |
| Agent Timeout | 60 seconds |
| Retry Attempts | 2 per agent (transient errors) |
| Cache TTL | 300 seconds (orchestrator) |
| SSE Stream Timeout | 180 seconds (frontend) |
| Token Refresh Interval | 50 minutes |
| Supported Crops | 8 (knowledge base) |
| Supported Diseases | 15 |
| Supported Pests | 6 |
| Supported Soil Types | 5 |
| Government Schemes | 10 |
| Gemini API Keys | Up to 11 (round-robin) |

---

## Innovation

SEED AI is distinguished by:

- **Autonomous multi-agent orchestration** with dynamic Gemini Function Calling routing
- **Hybrid vision pipeline** combining YOLO11, Gemma-4, Gemini Vision, Qwen2.5-VL, and HuggingFace models with automatic failover
- **Decision fusion** across multiple information sources with guardrails and reflection
- **Persistent farm memory** across sessions with async EventBus and Dead Letter Queue
- **Adaptive recommendations** that improve over time with farm history
- **Transparent reasoning** via SSE-streamed real-time execution
- **Multi-key Gemini pool** with round-robin, rate limiting, key cooldown, and g4f fallback
- **Production-grade multi-user isolation** at frontend, API, in-memory, and database layers
- **Zero-friction UX** with automatic context inference from text, memory, geolocation
- **Real-world agricultural applicability** backed by comprehensive knowledge base (8 crops, 15 diseases, 6 pests, 5 soils, 10 schemes, 40+ treatments, 26 crop MSPs)
- **Circuit breaker pattern** for frontend API resilience

---

## Conclusion

SEED AI demonstrates how autonomous AI agents can move beyond answering questions to coordinating complex agricultural decision-making. By combining computer vision, real-time weather intelligence, market insights, budget optimization, historical memory, and multilingual interaction within a unified multi-agent architecture, the platform delivers actionable, personalized farming guidance rather than isolated recommendations.

The project showcases the principles of modern AI agents — planning, reasoning, tool use, memory, reflection, guardrails, safety, and collaboration — in a real-world setting where timely, trustworthy decisions can improve productivity and support more sustainable agriculture. Built with production-grade security (multi-user isolation, circuit breaker, rate limiting, prompt sanitization), graceful degradation, and comprehensive documentation, SEED AI is a complete demonstration of the Google AI Agents: Intensive Vibe Coding Capstone Project requirements.

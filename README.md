# SEED AI
**Smart Ecosystem for Enhanced Agricultural Decisions**

SEED AI is an autonomous Multi-Agent agricultural platform designed for the Google AI Agents Capstone Project. It leverages Gemini Function Calling, Firebase, Supabase, and dynamic parallel execution to assist farmers with localized crop knowledge, disease detection, budget-aware treatment planning, weather risk analysis, and government scheme discovery.

## Key Features
- **Multi-Agent Architecture**: 10 dynamic Gemini-powered agents, orchestrated seamlessly.
- **Decision Fusion Engine**: Aggregates output from various agents into a synthesized recommendation.
- **Vision Integration**: Accepts leaf images securely via Supabase, analyzed by Gemini Vision.
- **Memory & Persistence**: Firestore-based memory allows the system to remember past interactions and crop history.
- **Real-Time Execution Transparency**: SSE (Server-Sent Events) streams live execution steps, tools used, and latencies directly to the Dashboard.

## Environment Setup
1. **Backend**: 
    - Requires Python 3.10+
    - Run `pip install -r requirements.txt` (ensure you are in `backend` dir)
    - Create a `.env` file containing:
      - `GEMINI_API_KEY`
      - `OPENWEATHER_API_KEY`
      - `DATA_GOV_IN_API_KEY`
      - `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` (or `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY`)
      - `GOOGLE_APPLICATION_CREDENTIALS` (path to Firebase service account json)
2. **Frontend**:
    - Requires Node.js 18+
    - Run `npm install` (ensure you are in `frontend` dir)

## Deployment Guide
1. Run backend locally via: `uvicorn main:app --reload --port 8000` from `backend/`.
2. Run frontend locally via: `npm run dev` from `frontend/`.
3. SEED AI supports graceful startup: if credentials (like Supabase or Firebase) are missing, it will disable those specific features (e.g. Vision upload, Memory logging) but the core LLM orchestration will continue to run.

## API Documentation
The API provides robust endpoints:
- `GET /api/health`: Comprehensive system health and capability breakdown.
- `POST /api/orchestrate`: Accepts JSON payloads for standard text queries and streams back SSE events.
- `POST /api/orchestrate/upload`: Accepts Multipart Form Data for processing image uploads, returning the same SSE event stream.
- `GET /api/evaluation/traces`: Returns stored execution evaluations and latencies for benchmarking.

## Testing
- Backend tests can be run using `python -m pytest tests/`
- All mocked data has been replaced with live API calls where valid credentials exist.

*Built for the Google AI Agents Capstone Project.*

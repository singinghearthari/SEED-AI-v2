# SEED AI - 5-Minute Demo Script (Capstone Project)

## Setup (Before starting)
1. Ensure the frontend (`npm run dev`) and backend (`uvicorn main:app --reload`) are running.
2. Have a sample leaf image ready (e.g., a tomato leaf with early blight).
3. Open the browser to `http://localhost:3000`.

## 0:00 - 1:00: Introduction & Dashboard Overview
- **Speaker:** "Welcome to SEED AI, our autonomous Multi-Agent agricultural platform. SEED AI is designed to help farmers make data-driven decisions by combining local crop knowledge, real-time market data, weather forecasts, and visual disease detection."
- **Action:** Show the main Dashboard. Highlight the "Agent Fleet" and "Feature Matrix" to show the active agents (e.g., Vision, Weather, Budget) and system health (Firebase, Supabase).

## 1:00 - 2:30: The Core Scenario (Image Upload & Query)
- **Speaker:** "Let's run a realistic scenario. A farmer in Bangalore has 3 acres of tomatoes and a budget of ₹4000. They've noticed some spots on their leaves and they upload an image."
- **Action:** 
  1. In the input box, type: `I have three acres of tomatoes. Budget ₹4000. Rain expected tomorrow.`
  2. Enter Location: `Bangalore`, Crop: `Tomato`, Budget: `4000`.
  3. Drag and drop the infected tomato leaf image into the upload area.
  4. Click **Run SEED AI**.

## 2:30 - 3:30: Execution Transparency (SSE Stream)
- **Speaker:** "As soon as we click run, SEED AI's Orchestrator agent evaluates the request. Notice the live execution trace."
- **Action:** Point to the "Live Execution Trace" panel as it populates.
- **Speaker:** "First, the image is securely uploaded to Supabase. Then, the Orchestrator uses Gemini Function Calling to dynamically decide which sub-agents to invoke. Because we uploaded an image and mentioned budget/weather, it spins up the Vision, Weather, and Budget agents in parallel. You can see the latencies and tools used in real-time."

## 3:30 - 4:30: Decision Fusion & Results
- **Speaker:** "Once the agents finish, the Decision Fusion engine synthesizes their findings into a cohesive, safe recommendation, which is then verified by a Reflection engine."
- **Action:** Scroll to the "AI Recommendation" results card.
- **Speaker:** "The Vision agent identified the disease. The Weather agent cross-referenced the rain forecast, advising us to delay spraying pesticides to avoid runoff. The Budget agent ensured the recommended fungicide fits within our ₹4000 limit. We also get clear 'Alternatives Considered' and 'Follow-up Actions'."

## 4:30 - 5:00: Memory & Conclusion
- **Speaker:** "Behind the scenes, this entire interaction, including the detected disease and treatment, is logged into the farmer's Firestore Farm Memory. The next time they ask a question, SEED AI will remember this exact context."
- **Action:** Show the "Agent Execution Details" JSON block briefly to prove the structured data is real.
- **Speaker:** "Thank you for watching the SEED AI demo. We've built a robust, explainable, and context-aware platform ready to assist farmers on the ground."

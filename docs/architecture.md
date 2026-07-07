# SEED AI Architecture

This document contains Mermaid diagrams illustrating the core architectural flows of SEED AI.

## 1. Overall System Architecture

```mermaid
graph TD
    subgraph Frontend [Next.js Frontend]
        UI[User Interface]
        SSE[SSE Client]
        Upload[Image Upload component]
    end

    subgraph Backend [FastAPI Backend]
        API[API Router]
        Orchestrator[Orchestrator Agent]
        Eval[Evaluation Engine]
        
        subgraph Agents
            Vision[Vision Agent]
            Weather[Weather Agent]
            Market[Market Agent]
            Budget[Budget Agent]
            Crop[Crop Knowledge Agent]
            Gov[Gov Schemes Agent]
            Task[Task Planning Agent]
        end
    end

    subgraph External Services
        Gemini[Google Gemini API]
        Supabase[(Supabase Storage)]
        Firebase[(Firestore / Auth)]
        WeatherAPI[OpenWeatherMap]
        GovAPI[Data.gov.in API]
    end

    UI -->|JSON Request| API
    Upload -->|Multipart Form| API
    API --> Orchestrator
    
    Orchestrator -->|Streams Events| SSE
    SSE --> UI
    
    Orchestrator -.->|Uploads Image| Supabase
    Orchestrator -->|Function Calling| Gemini
    
    Orchestrator --> Vision
    Orchestrator --> Weather
    Orchestrator --> Market
    Orchestrator --> Budget
    Orchestrator --> Crop
    Orchestrator --> Gov
    Orchestrator --> Task

    Vision --> Gemini
    Crop --> Gemini
    Weather --> WeatherAPI
    Gov --> GovAPI
    
    Orchestrator -->|Memory Retrieval/Update| Firebase
```

## 2. Decision Fusion Workflow

```mermaid
sequenceDiagram
    participant User
    participant Orchestrator
    participant Gemini Function Calling
    participant Agents
    participant Decision Fusion
    participant Reflection

    User->>Orchestrator: Farm Query + Optional Image
    Orchestrator->>Gemini Function Calling: Evaluate context & determine tools
    Gemini Function Calling-->>Orchestrator: List of required agents
    
    par Parallel Agent Execution
        Orchestrator->>Agents: Execute selected agents (e.g. Vision, Weather, Budget)
        Agents-->>Orchestrator: Agent specific recommendations
    end

    Orchestrator->>Decision Fusion: Send aggregated agent data
    Decision Fusion-->>Orchestrator: Structured FusionResult (Draft)

    Orchestrator->>Reflection: Send FusionResult for critique
    Reflection-->>Orchestrator: Revised FusionResult (Safe & Consistent)

    Orchestrator->>User: Final Recommendation
```

## 3. Storage Flow

```mermaid
graph LR
    A[Frontend] -->|Image Upload| B(FastAPI Backend)
    B -->|Validate MIME & Size| C{Validation Pass?}
    C -->|Yes| D[Supabase Storage]
    C -->|No| E[Reject]
    D -->|Return Signed URL & Path| B
    B -->|Base64 or URL| F[Vision Agent]
    F -->|Analysis| G[Gemini Vision Model]
```

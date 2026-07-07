# Firestore Database Schemas

This document defines the schema for the persistent data collections stored in Firebase Firestore for SEED AI.

## 1. `users`
Stores user profile information.
```json
{
  "uid": "string (Firebase Auth UID)",
  "email": "string",
  "created_at": "timestamp",
  "preferences": {
    "language": "string",
    "notifications_enabled": "boolean"
  }
}
```

## 2. `farm_memory`
Stores high-level persistent memory about a specific farmer's fields to maintain context across sessions.
```json
{
  "user_id": "string",
  "crop": "string",
  "location": "string",
  "last_query": "string",
  "last_recommendation": "object (FusionResult)",
  "updated_at": "timestamp"
}
```

## 3. `disease_history`
Tracks diseases detected by the Vision agent for a user over time.
```json
{
  "user_id": "string",
  "disease": "string",
  "crop": "string",
  "severity": "string",
  "confidence": "number",
  "image_path": "string (Supabase Storage path)",
  "timestamp": "timestamp"
}
```

## 4. `conversation_history`
Logs all conversations/requests and the recommendations provided by SEED AI.
```json
{
  "user_id": "string",
  "query": "string",
  "recommendation": "object (FusionResult)",
  "agents_used": ["string"],
  "confidence": "string",
  "timestamp": "timestamp"
}
```

## 5. `execution_logs`
(Optional / For Admin) Detailed traces of agent executions and API latencies for Evaluation & Benchmarking (Phase E).
```json
{
  "trace_id": "string",
  "user_id": "string",
  "total_latency_ms": "number",
  "status": "string (completed/failed)",
  "agents_invoked": [
    {
      "agent": "string",
      "latency_sec": "number",
      "success": "boolean"
    }
  ],
  "timestamp": "timestamp"
}
```

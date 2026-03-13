# ADR-013: Session-Based Stateless Architecture

## Status
Accepted

## Context
Each career analysis involves a multi-step flow: create session → upload resume → add jobs → run analysis → explore results → chat. The backend must track state across these steps while remaining horizontally scalable for Cloud Run (multiple instances, scale to zero).

## Decision
Use a session-based architecture with UUID-keyed sessions:

- **Session creation**: `POST /api/v1/session` returns a UUID
- **Session lifecycle**: Upload, analyze, and chat operations reference the session ID
- **State storage**: Currently in-memory (suitable for single-instance dev); Neo4j stores persistent analysis results
- **Session cleanup**: Periodic deletion of old sessions
- **Max constraints**: 5 jobs per session, 10MB file size, 50k chars content

WebSocket connections use the session ID for progress streaming: `WS /ws/progress/{session_id}`.

Future migration path: Redis for session state when horizontal scaling is needed.

Alternatives considered:
- **JWT-based stateless**: No server-side state, but analysis results are too large for tokens; requires external storage anyway
- **Redis from day one**: Better for multi-instance, but adds infrastructure complexity before it's needed
- **Database-backed sessions**: Neo4j could store session state, but adds latency for frequent updates during analysis

## Consequences
- **Easier**: Simple UUID-based routing; no external session store needed for single instance; clean API design; WebSocket integration straightforward; Cloud Run compatible
- **Harder**: In-memory state is lost on instance restart; horizontal scaling requires Redis migration; no session persistence across deploys; concurrent session limit tied to memory

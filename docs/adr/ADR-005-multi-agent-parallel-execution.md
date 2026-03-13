# ADR-005: Multi-Agent Parallel Execution Architecture

## Status
Accepted

## Context
Career analysis involves 7 distinct AI tasks (resume parsing, JD analysis, skill matching, recommendations, interview prep, market insights, chat). Sequential execution would take 75-120 seconds total. Users expect near-real-time feedback.

The agents have natural dependency boundaries:
- Phase 1 (parsing) has no dependencies — resume and JD parsing are independent
- Phase 2 (matching) depends on Phase 1 outputs — but multiple jobs can match in parallel
- Phase 3 (analysis) depends on Phase 2 — but recommendation, interview prep, and market insights are independent

## Decision
Implement a 3-phase parallel execution model using `asyncio.gather()` within LlamaIndex workflows:

```
Phase 1: asyncio.gather(resume_parser, jd_analyzer * N)    → 15-25s
Phase 2: asyncio.gather(skill_matcher * N jobs)             → 10-20s
Phase 3: asyncio.gather(recommendation, interview, market)  → 10-15s
```

All agents inherit from `BaseAgent` with a strict contract:
- `input_schema` / `output_schema`: Pydantic models for validation
- `process(input_data)`: Main async logic returning `AgentOutput`
- `health_check()`: Diagnostic method
- `report_progress()`: WebSocket progress updates

Real-time progress is streamed via WebSocket (`/ws/progress/{session_id}`) so the frontend can show per-agent status.

## Consequences
- **Easier**: 60-70% faster total execution; clear dependency boundaries; each agent is independently testable; WebSocket provides real-time UX; BaseAgent contract ensures consistency
- **Harder**: Debugging parallel failures requires structured logging; error in one agent must not crash sibling agents; state management across phases requires careful orchestration via LlamaIndex workflow context (`ctx.store`)

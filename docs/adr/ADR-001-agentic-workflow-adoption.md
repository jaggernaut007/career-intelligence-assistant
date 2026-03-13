# ADR-001: Adopt Agentic Coding Workflow

## Status
Accepted

## Context
The project has grown to include 8 AI agents, 6 services, a React frontend, and Neo4j integration. Development velocity and code quality need to scale with the codebase. IDE coding agents (Claude Code, Copilot) are used daily. Without structured agent instructions, context management, and verification gates, agent-generated code quality degrades.

## Decision
Adopt the agentic coding workflow defined in `docs/agentic-guide-v2.md`. This includes:
- AGENTS.md + CLAUDE.md for agent instruction architecture
- PROGRESS.md for cross-session state
- `scripts/init.sh` for session start verification
- `.claude/hooks.json` for automated lint/test enforcement
- `.claude/skills/` for modular on-demand knowledge (session-handoff, commit-ready)
- `.claude/agents/` for specialised subagents (code-reviewer, test-writer, research-assistant, docs-writer)
- `.claude/rules/` for path-scoped coding standards
- `docs/adr/` for architecture decision records
- `docs/research/` for pre-implementation research notes

## Consequences
- **Easier**: consistent code quality, cross-session continuity, structured verification, team onboarding
- **Harder**: initial setup overhead, maintaining PROGRESS.md and research notes, learning new workflow

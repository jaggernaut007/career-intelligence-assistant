@import AGENTS.md

## Claude-Specific Behaviours

### Subagent Routing
- Use the Explore subagent for read-only codebase search
- Use the Plan subagent before implementing anything with 3+ steps or multi-file changes
- Use code-reviewer agent after every implementation wave
- Use test-writer agent for new feature coverage
- Spawn subagents only when the task benefits from isolated context

### Context Management
- When context feels crowded, stop and write a summary to PROGRESS.md
- Start fresh sessions for new features (`/clear` after every commit)
- Use `/compact focus on X` for focused sessions within a broader task
- If uncertain about a past decision, check `docs/adr/` before guessing

### Nexus-MCP Code Intelligence
Use Nexus-MCP actively for codebase understanding instead of manual grep/read loops:
- `search` — hybrid semantic+keyword+graph search for discovering relevant code ("find rate limiting logic")
- `find_symbol` — look up any function/class by name to get definition and relationships
- `find_callers` / `find_callees` — trace call graphs before modifying a function
- `impact` — run transitive change impact analysis before any refactor or API change
- `explain` — get combined graph+vector explanation of what a symbol does and how it's used
- `analyze` — check complexity, dependencies, code smells, and quality score for a path
- `architecture` — get high-level architectural overview (layers, dependencies, entry points)
- `overview` — get project stats (languages, file counts, symbol counts, quality summary)
- `remember` / `recall` — persist and retrieve semantic memories across sessions

**When to use**: Before modifying any function, run `find_callers` + `impact` to understand blast radius. Before implementing new features, run `search` to find existing patterns. At session start, run `overview` to orient. Use `explain` instead of manually reading multiple files to understand a symbol.

### Hallucination Prevention
- For any external library or API, check MCP docs servers first
- If MCP does not cover it, check `docs/research/` for an existing research note
- If no research note exists, perform a web search for current official docs
- Pin library versions in all research queries
- Use Nexus-MCP `search` to find existing codebase patterns before inventing new ones

### Security
- Run Snyk security scan for new first-party code in a supported language
- Apply guardrails (InputValidator, PromptGuard) before all LLM calls
- Apply PIIDetector and OutputFilter before returning data to users
- Verify packages exist in public registries before adding dependencies

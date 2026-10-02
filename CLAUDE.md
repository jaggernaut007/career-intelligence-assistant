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
- The nexus tools are deferred. Run ToolSearch with `select:mcp__nexus__index,mcp__nexus__search,mcp__nexus__map,mcp__nexus__find_symbol,mcp__nexus__graph,mcp__nexus__explain`.
- At session start, call `index` with the absolute path of the working folder.
- To find files or code, call `search` or `find_symbol` before Grep or Glob. Read only the files that nexus names.
- Before you change a shared symbol, call `graph` with `transitive=true`.
- The current tools are `status`, `index`, `map`, `search`, `find_symbol`, `graph`, `explain`, `analyze`, `memory` and `health`.

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

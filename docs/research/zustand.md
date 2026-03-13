# Research: Zustand
**Library version:** `zustand@^4.5.0`
**Latest available:** 5.0.11 (released 2026-02-01) / 4.5.7 (latest v4 LTS, released 2025-05-15)
**Status:** Needs update -- v5 is stable and current; v4 still receives backports but is legacy

## Sources Consulted
| Source | URL | Date accessed |
|--------|-----|---------------|
| npm registry | https://registry.npmjs.org/zustand | 2026-03-13 |
| GitHub releases | https://github.com/pmndrs/zustand/releases | 2026-03-13 |
| GitHub repo stats | https://api.github.com/repos/pmndrs/zustand | 2026-03-13 |
| OSV vulnerability DB | https://api.osv.dev/v1/query (ecosystem: npm, package: zustand) | 2026-03-13 |

## The Correct Approach
The project uses zustand correctly with three well-scoped stores following the single-responsibility principle:

- **sessionStore** -- session lifecycle (create, clear, error state)
- **wizardStore** -- multi-step wizard navigation and analysis progress tracking
- **analysisStore** -- parsed resume/job data and all analysis results

Current patterns that are correct:
```typescript
// Typed store with create<Interface> generic -- correct for v4 and v5
export const useSessionStore = create<SessionStore>((set) => ({ ... }));

// Atomic selectors to avoid unnecessary re-renders -- correct
const setSession = useSessionStore((s) => s.setSession);

// getState() for reading outside React render cycle -- correct
const state = useAnalysisStore.getState();
```

The stores use no middleware (no persist, devtools, immer), which keeps them simple. The `initialState` pattern with `reset()` in wizardStore and analysisStore is a clean approach for clearing state.

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|----------|-------------|
| Redux Toolkit | Excessive boilerplate for 3 small stores; zustand's API is more concise for this scale |
| Jotai (atomic model) | The project's state is store-shaped, not atom-shaped; wizard flow benefits from grouped state |
| Valtio (proxy model) | Proxy-based reactivity adds complexity; the project's stores are simple enough for zustand's immutable model |
| React Context alone | Would cause unnecessary re-renders without careful memoization; zustand handles this out of the box with selectors |
| Combining all state into one store | Violates single-responsibility; separate stores allow independent subscriptions |

## Security Assessment
- [x] CVE check -- **No known CVEs.** OSV database returns 0 vulnerabilities for zustand (all versions). GitHub Security Advisories show no zustand-specific issues.
- [x] Maintenance health -- **Excellent.** Part of the pmndrs (Poimandres) ecosystem. 57,365 GitHub stars, 1,974 forks, only 5 open issues. Last push: 2026-03-09. Active release cadence: 11 stable v5 releases since Oct 2024, plus continued v4.x backports.
- [x] License compatibility -- **MIT License.** Fully permissive, no concerns.
- [x] Dependency tree risk -- **Minimal.** Zustand has near-zero dependencies (only `use-sync-external-store` for React 18 compatibility). Very small attack surface.

## Known Gotchas / Edge Cases

### v5 Breaking Changes (critical if upgrading from ^4.5.0)
Zustand v5 was released 2024-10-14. Key breaking changes:

1. **No more default export.** `import create from 'zustand'` becomes `import { create } from 'zustand'`. The project already uses named imports, so this is a non-issue.

2. **`create` requires a function argument.** `create()(...)` (curried empty call) is removed. The project uses `create<T>((set) => ({...}))` directly -- no change needed.

3. **`setState` replaces by default instead of merging.** In v4, `set({ foo: 1 })` merges with existing state. In v5, the default behavior changed. You must pass `true` as a second argument or use the `merge` option. **This is the highest-risk breaking change for this project** since the stores rely heavily on partial `set()` calls like `set({ error: null })`.

4. **TypeScript: `create` no longer infers the store type from the initial state alone.** Must use `create<StoreType>()` -- which the project already does.

5. **Middleware type signatures changed.** Not applicable since the project uses no middleware.

6. **`useStore` hook removed from main export.** Use `create` with selectors instead. The project does not use `useStore` directly.

### TypeScript Gotchas
- Always provide the full store interface as a generic to `create<T>()`. Relying on inference can produce overly narrow types, especially with `set()` partial updates.
- When using `getState()` outside components (as in `analysisStore.addJob`), the return type is correctly inferred but be cautious: mutations via `getState()` do not trigger React re-renders.

### Store Composition
- Zustand stores are independent singletons. Cross-store reads (as in `hooks.ts` where `useSessionStore` and `useAnalysisStore` are read from the same hook) work fine because each `useStore(selector)` call is an independent subscription.
- For cross-store writes, the project correctly calls `set()` from one store's action while reading another store via `getState()`. This is the recommended pattern.

### React 18 Concurrent Mode
- Zustand v4.5+ and v5 both use `useSyncExternalStore` internally, which is the React 18 concurrent-safe way to subscribe to external stores. No tearing issues.
- The project wraps the app in `<React.StrictMode>`, which exercises concurrent features in development. No special configuration needed.

### Performance Considerations
- The project correctly uses atomic selectors (`(s) => s.setSession`) rather than returning the full store object. This prevents unnecessary re-renders.
- The `agentStatuses` array in wizardStore creates new array references on every update. If components subscribe to the full array, they will re-render on every agent status change. Consider a selector that picks a specific agent's status if this becomes a bottleneck.

### Upgrade Recommendation
The project is on `^4.5.0` (resolves up to 4.5.7). Upgrading to v5 is recommended but requires auditing all `set()` calls to ensure partial merging still works correctly. The migration is low-risk for this codebase since:
- Named imports already used
- Typed `create<T>()` already used
- No middleware in use
- Only 3 small stores to audit

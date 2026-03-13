# Research: TanStack React Query
**Library version:** `@tanstack/react-query@^5.17.0`
**Latest available:** 5.90.21 (released 2026-02-11)
**Status:** Current -- on the correct major version; minor updates recommended

## Sources Consulted
| Source | URL | Date accessed |
|--------|-----|---------------|
| npm registry | https://registry.npmjs.org/@tanstack/react-query | 2026-03-13 |
| GitHub releases | https://github.com/TanStack/query/releases | 2026-03-13 |
| GitHub repo stats | https://api.github.com/repos/TanStack/query | 2026-03-13 |
| OSV vulnerability DB | https://api.osv.dev/v1/query (ecosystem: npm, package: @tanstack/react-query) | 2026-03-13 |

## The Correct Approach
The project uses React Query correctly for server state management, separating concerns between:
- **Zustand** for client-side UI state (wizard steps, selected items, local flags)
- **React Query** for server state (API calls, caching, polling)

Current patterns in use:

```typescript
// QueryClient with sensible defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 min stale time -- good for analysis data
      retry: 1,                    // Single retry -- appropriate for LLM backends
    },
  },
});

// useMutation for write operations (session create, uploads, analysis start)
useMutation({ mutationFn: async () => { ... }, onSuccess, onError });

// useQuery with polling for long-running analysis
useQuery({
  queryKey: ['analysis', sessionId],
  enabled: enabled && !!sessionId,
  refetchInterval: (query) => {
    // Stop polling when complete/failed
    if (data?.status === 'completed' || data?.status === 'failed') return false;
    return 2000;
  },
});

// useQuery with composite keys for per-job data
useQuery({ queryKey: ['recommendations', sessionId, jobId], ... });
```

The use of `enabled` flags to conditionally fire queries and composite `queryKey` arrays for cache granularity are both correct v5 patterns.

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|----------|-------------|
| SWR | Less feature-rich for mutations; lacks built-in devtools; TanStack Query has better TypeScript support and more active ecosystem |
| Plain Axios + useEffect | Manual cache management, no deduplication, no background refetching, no retry logic; would require reimplementing what React Query provides |
| RTK Query (Redux Toolkit) | Would require Redux as a dependency; overkill when not using Redux for client state |
| Apollo Client | GraphQL-focused; the project uses REST APIs |
| Storing server data in Zustand | Conflates server state with client state; loses automatic cache invalidation, stale-while-revalidate, and background refetching |

## Security Assessment
- [x] CVE check -- **No known CVEs.** OSV database returns 0 vulnerabilities for @tanstack/react-query (all versions).
- [x] Maintenance health -- **Excellent.** 48,799 GitHub stars, 3,730 forks. 175 open issues (normal for a library this size). Last push: 2026-03-13 (today). 285 stable v5 releases since Oct 2023. Maintained by Tanner Linsley and an active team. Very high release cadence (multiple releases per month).
- [x] License compatibility -- **MIT License.** Fully permissive, no concerns.
- [x] Dependency tree risk -- **Low.** Core dependency is `@tanstack/query-core`. Small, focused dependency tree.

## Known Gotchas / Edge Cases

### Changes Since 5.17.0
The project pins `^5.17.0`, which means it can resolve up to 5.90.21. The v5 line has been entirely semver-minor/patch since 5.0.0, so there are no breaking changes within the `^5` range. Notable additions since 5.17:

1. **Improved `refetchInterval` callback signature.** The project uses `refetchInterval: (query) => { ... }` which is the current v5 API. In earlier v5 releases this received `(data, query)` -- the project's usage with `query.state.data` is correct for current versions.

2. **Better TypeScript inference.** Later v5 releases improved generic inference for `useQuery` and `useMutation`. No code changes needed but types become more precise.

3. **New `throwOnError` option** replaces `useErrorBoundary`. The project does not use error boundaries for queries, so no impact.

4. **`queryClient.getQueryData` type narrowing improvements.** Helpful if the project ever reads cache directly.

### Cache Invalidation Patterns
- The project does **not** currently invalidate queries after mutations. For example, after `useUploadResume` succeeds, the analysis cache is not invalidated. This is acceptable because the analysis hasn't started yet, but consider adding `queryClient.invalidateQueries({ queryKey: ['analysis'] })` in the `useStartAnalysis` `onSuccess` callback for robustness.
- Composite query keys like `['recommendations', sessionId, jobId]` correctly scope cache entries per session and job. Invalidating all recommendations for a session can be done with `invalidateQueries({ queryKey: ['recommendations', sessionId] })` (prefix matching).

### Polling Pattern
- The `refetchInterval` approach for polling analysis results is correct. The callback stops polling when `status === 'completed' || 'failed'`.
- **Gotcha:** If the user navigates away and back, the query may restart polling from scratch if the component unmounts and remounts. The `enabled` flag mitigates this by requiring explicit opt-in.
- **Gotcha:** The 2-second polling interval is reasonable for LLM analysis but be aware that each poll is a full API call. If the backend is under load, consider exponential backoff or WebSocket-based completion notifications (the project already has a WebSocket hook).

### WebSocket Integration
- The project has `useWebSocket.ts` for real-time updates. React Query and WebSockets can coexist: use WebSocket events to call `queryClient.setQueryData()` or `queryClient.invalidateQueries()` to keep the cache in sync without polling.
- Currently the polling approach and WebSocket hook appear to be parallel systems. Consider consolidating: use WebSocket for push notifications, then `invalidateQueries` to trigger a fresh fetch.

### Side Effects in queryFn
- The `useAnalysisResults` hook performs side effects (setting zustand store state) inside the `queryFn`. This works but is unconventional -- side effects are typically in `onSuccess`. However, in React Query v5, `onSuccess` on `useQuery` was **removed** (it was removed in v5.0.0). The project's approach of handling side effects in `queryFn` is the correct v5 pattern. The code comment "Handle side effects here instead of onSuccess" confirms awareness of this.

### Mutations and Optimistic Updates
- The project does not use optimistic updates. Given that operations involve LLM processing (5-minute timeout on resume upload), optimistic updates would not be appropriate. The current approach of updating stores in `onSuccess` is correct.

### React StrictMode Double-Firing
- In development with StrictMode, queries and mutations may fire twice. This is expected React 18 behavior. The project should ensure that side effects in `queryFn` are idempotent (they are -- `setResume`, `setSession`, etc. are simple state replacements).

### Upgrade Recommendation
The project is on `^5.17.0` and will auto-resolve to latest 5.x on fresh install. No action needed for major version. Consider pinning to a narrower range (e.g., `~5.90.0`) if stability is preferred over auto-updates, since the v5 line moves very fast (285 releases in ~2.5 years).

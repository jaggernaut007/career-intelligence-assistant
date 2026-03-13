# ADR-007: React + Vite + TypeScript + Zustand Frontend

## Status
Accepted

## Context
The frontend requires:
- A multi-step wizard (upload → add jobs → analysis → explore results)
- Real-time progress updates via WebSocket during agent execution
- Data visualization (fit scores, skill gaps, market insights charts)
- Type safety for complex state management across stores
- Fast development iteration with hot module replacement

## Decision
Use the following frontend stack:

| Technology | Version | Purpose |
|-----------|---------|---------|
| React | 18.2.0 | UI framework (functional components, hooks) |
| TypeScript | 5.3.3 | Type safety across all components and stores |
| Vite | 5.1.0 | Build tool (instant HMR, fast builds) |
| Zustand | 4.5.0 | Client state (session, wizard, analysis stores) |
| React Query | 5.17.0 | Server state (API caching, mutations, retry) |
| Tailwind CSS | 3.4.1 | Utility-first styling |
| Framer Motion | 11.0.3 | Animations and transitions |
| Recharts | 2.12.0 | Data visualization (fit scores, market charts) |
| DOMPurify | 3.0.8 | HTML sanitization for rendered markdown |
| Axios | 1.6.7 | HTTP client |

**State architecture**: Zustand manages UI state (3 stores: session, wizard, analysis). React Query manages server state (caching, refetching, optimistic updates). WebSocket hook updates Zustand stores in real-time.

Alternatives considered:
- **Next.js**: SSR unnecessary for this SPA; adds complexity without benefit
- **Redux**: More boilerplate than Zustand; ~1KB vs ~50KB; no Provider wrapper needed
- **SWR**: Less feature-rich than React Query for mutations and cache management
- **MUI/Chakra**: Heavier than Tailwind; slower iteration on custom designs

## Consequences
- **Easier**: Zustand is minimal (~1KB); Vite gives instant HMR; TypeScript catches state shape errors at compile time; Tailwind enables rapid UI iteration; React Query handles caching and retry automatically
- **Harder**: No component library (building all UI from scratch with Tailwind); Zustand has less ecosystem tooling than Redux; Recharts has limited chart types compared to D3

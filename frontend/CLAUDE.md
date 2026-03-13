# Frontend — Claude Context

## Architecture
- React 18 + TypeScript + Vite entry: `src/main.tsx`
- Three Zustand stores: wizard, analysis, session (`src/store/`)
- React Query for data fetching (`src/api/`)
- WebSocket hook for real-time updates (`src/hooks/useWebSocket.ts`)

## Key Patterns
- Functional components with TypeScript props
- Tailwind CSS + clsx + tailwind-merge for styling
- DOMPurify for HTML sanitization before rendering
- Direct imports only (no barrel files)
- Components organized by feature: chat/, results/, wizard/, common/, ui/

## Testing
- `npx vitest run` for all tests
- Testing Library for component rendering
- MSW for API mocking
- Tests colocated in `__tests__/` directories

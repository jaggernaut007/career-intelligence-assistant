# State Management

The Career Intelligence Assistant uses [Zustand](https://zustand-demo.pmnd.rs/) for lightweight state management combined with [React Query](https://tanstack.com/query/latest) for server state.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                          Components                              │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
            ┌───────▼───────┐           ┌───────▼───────┐
            │    Zustand    │           │  React Query  │
            │  (UI State)   │           │ (Server State)│
            └───────────────┘           └───────────────┘
                    │                           │
                    │                     ┌─────▼─────┐
                    │                     │  Axios    │
                    │                     │  Client   │
                    │                     └─────┬─────┘
                    │                           │
                    │                     ┌─────▼─────┐
                    │                     │  Backend  │
                    │                     │   API     │
                    │                     └───────────┘
                    │
            ┌───────▼───────┐
            │ sessionStorage│
            │  (Persistence)│
            └───────────────┘
```

---

## Zustand Stores

### Session Store

**Location**: `frontend/src/store/sessionStore.ts`

Manages the user's analysis session lifecycle.

```typescript
interface SessionStore {
  session: Session | null;
  isInitializing: boolean;
  error: string | null;

  setSession: (session: Session) => void;
  setInitializing: (initializing: boolean) => void;
  setError: (error: string | null) => void;
  clearSession: () => void;
}
```

**State Shape**:
| Field | Type | Description |
|-------|------|-------------|
| `session` | `Session \| null` | Current session object with ID |
| `isInitializing` | `boolean` | True while creating session |
| `error` | `string \| null` | Error message if session failed |

**Persistence**: Session ID is stored in `sessionStorage` for page refreshes.

**Usage**:
```tsx
import { useSessionStore } from '@/store/sessionStore';

function MyComponent() {
  const { session, setSession, clearSession } = useSessionStore();

  // Access session
  if (session) {
    console.log(session.sessionId);
  }

  // Clear on logout
  clearSession();
}
```

---

### Wizard Store

**Location**: `frontend/src/store/wizardStore.ts`

Controls the multi-step wizard flow and analysis progress.

```typescript
interface WizardStore {
  currentStep: WizardStep;          // 1-4
  canProceed: boolean;
  isAnalyzing: boolean;
  agentStatuses: AgentStatusUpdate[];
  error: string | null;

  setStep: (step: WizardStep) => void;
  nextStep: () => void;
  prevStep: () => void;
  setCanProceed: (can: boolean) => void;
  setAnalyzing: (analyzing: boolean) => void;
  updateAgentStatus: (update: AgentStatusUpdate) => void;
  clearAgentStatuses: () => void;
  setError: (error: string | null) => void;
  reset: () => void;
}
```

**Wizard Steps**:
| Step | Name | Description |
|------|------|-------------|
| 1 | Upload | Resume upload |
| 2 | Jobs | Add job descriptions |
| 3 | Analysis | Run analysis (shows progress) |
| 4 | Explore | View results |

**State Shape**:
| Field | Type | Description |
|-------|------|-------------|
| `currentStep` | `1 \| 2 \| 3 \| 4` | Current wizard step |
| `canProceed` | `boolean` | Whether user can advance |
| `isAnalyzing` | `boolean` | True during analysis |
| `agentStatuses` | `AgentStatusUpdate[]` | Real-time agent progress |
| `error` | `string \| null` | Error message |

**Agent Status Update**:
```typescript
interface AgentStatusUpdate {
  agentName: string;      // "resume_parser", "skill_matcher", etc.
  status: "pending" | "running" | "completed" | "failed";
  progress: number;       // 0-100
  currentStep?: string;   // "Processing extracted data"
  error?: string;
}
```

**Usage**:
```tsx
import { useWizardStore } from '@/store/wizardStore';

function WizardNavigation() {
  const { currentStep, canProceed, nextStep, prevStep } = useWizardStore();

  return (
    <>
      <button onClick={prevStep} disabled={currentStep === 1}>Back</button>
      <button onClick={nextStep} disabled={!canProceed}>Next</button>
    </>
  );
}

function AnalysisProgress() {
  const { agentStatuses } = useWizardStore();

  return (
    <ul>
      {agentStatuses.map(agent => (
        <li key={agent.agentName}>
          {agent.agentName}: {agent.progress}%
        </li>
      ))}
    </ul>
  );
}
```

---

### Analysis Store

**Location**: `frontend/src/store/analysisStore.ts`

Stores all analysis data: resume, jobs, results, and insights.

```typescript
interface AnalysisStore {
  resume: ParsedResume | null;
  jobDescriptions: ParsedJobDescription[];
  analysisResult: AnalysisResult | null;
  selectedJobId: string | null;
  recommendations: RecommendationResult | null;
  interviewPrep: InterviewPrepResult | null;
  marketInsights: MarketInsightsResult | null;

  setResume: (resume: ParsedResume) => void;
  addJob: (job: ParsedJobDescription) => void;
  removeJob: (jobId: string) => void;
  setAnalysisResult: (result: AnalysisResult) => void;
  setSelectedJob: (jobId: string | null) => void;
  setRecommendations: (recommendations: RecommendationResult) => void;
  setInterviewPrep: (interviewPrep: InterviewPrepResult) => void;
  setMarketInsights: (marketInsights: MarketInsightsResult) => void;
  clearAll: () => void;
}
```

**State Shape**:
| Field | Type | Description |
|-------|------|-------------|
| `resume` | `ParsedResume \| null` | Uploaded resume data |
| `jobDescriptions` | `ParsedJobDescription[]` | Added jobs (max 5) |
| `analysisResult` | `AnalysisResult \| null` | Fit scores and gaps |
| `selectedJobId` | `string \| null` | Currently selected job for detail view |
| `recommendations` | `RecommendationResult \| null` | Improvement suggestions |
| `interviewPrep` | `InterviewPrepResult \| null` | Interview questions |
| `marketInsights` | `MarketInsightsResult \| null` | Salary/market data |

**Job Limit**: Maximum 5 jobs per session (enforced in `addJob`).

**Usage**:
```tsx
import { useAnalysisStore } from '@/store/analysisStore';

function JobList() {
  const { jobDescriptions, removeJob, selectedJobId, setSelectedJob } = useAnalysisStore();

  return (
    <ul>
      {jobDescriptions.map(job => (
        <li
          key={job.id}
          className={job.id === selectedJobId ? 'selected' : ''}
          onClick={() => setSelectedJob(job.id)}
        >
          {job.title} at {job.company}
          <button onClick={() => removeJob(job.id)}>Remove</button>
        </li>
      ))}
    </ul>
  );
}

function FitScore() {
  const { analysisResult, selectedJobId } = useAnalysisStore();

  const match = analysisResult?.jobMatches.find(m => m.jobId === selectedJobId);

  return match ? <div>Fit Score: {match.fitScore}%</div> : null;
}
```

---

## React Query Patterns

Server state is managed via React Query hooks in `frontend/src/hooks/`.

### Query Keys

```typescript
const queryKeys = {
  session: ['session'],
  resume: (sessionId: string) => ['resume', sessionId],
  jobs: (sessionId: string) => ['jobs', sessionId],
  analysis: (sessionId: string) => ['analysis', sessionId],
  recommendations: (sessionId: string) => ['recommendations', sessionId],
  interviewPrep: (sessionId: string) => ['interview-prep', sessionId],
  marketInsights: (sessionId: string) => ['market-insights', sessionId],
};
```

### Example Hook

```typescript
// frontend/src/hooks/useAnalysis.ts
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { useSessionStore } from '@/store/sessionStore';
import { useAnalysisStore } from '@/store/analysisStore';

export function useStartAnalysis() {
  const queryClient = useQueryClient();
  const { session } = useSessionStore();
  const { setAnalysisResult } = useAnalysisStore();

  return useMutation({
    mutationFn: () => apiClient.startAnalysis(session!.sessionId),
    onSuccess: (data) => {
      setAnalysisResult(data);
      queryClient.invalidateQueries({ queryKey: ['analysis', session!.sessionId] });
    },
  });
}
```

---

## WebSocket Integration

Real-time progress updates are handled via WebSocket and update the wizard store.

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useEffect } from 'react';
import { useWizardStore } from '@/store/wizardStore';

export function useAnalysisProgress(sessionId: string | null) {
  const { updateAgentStatus, setAnalyzing } = useWizardStore();

  useEffect(() => {
    if (!sessionId) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/progress/${sessionId}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'agent_progress') {
        updateAgentStatus({
          agentName: data.agent_name,
          status: data.status,
          progress: data.progress,
          currentStep: data.current_step,
          error: data.error,
        });
      }

      if (data.type === 'analysis_complete') {
        setAnalyzing(false);
      }
    };

    return () => ws.close();
  }, [sessionId]);
}
```

---

## State Flow Diagram

```
User Action                    Store Updates                  UI Updates
─────────────────────────────────────────────────────────────────────────
Upload Resume    ──►  sessionStore.setSession()    ──►  Show success
                      analysisStore.setResume()         Enable "Next"
                      wizardStore.setCanProceed(true)

Add Job          ──►  analysisStore.addJob()       ──►  Show job card
                      wizardStore.setCanProceed(true)   Update count

Start Analysis   ──►  wizardStore.setAnalyzing(true) ──► Show progress
                      wizardStore.setStep(3)            Disable nav

WebSocket msg    ──►  wizardStore.updateAgentStatus() ──► Update bars

Analysis Done    ──►  analysisStore.setAnalysisResult() ──► Show results
                      wizardStore.setStep(4)              Enable explore
                      wizardStore.setAnalyzing(false)
```

---

## Best Practices

1. **Keep stores focused** - Each store has a single responsibility
2. **Use selectors** - Subscribe only to needed state slices
3. **Derive state** - Calculate values in components, not stores
4. **Clear on unmount** - Reset stores when session ends

```tsx
// Good: Subscribe to specific slice
const sessionId = useSessionStore(state => state.session?.sessionId);

// Bad: Subscribe to entire store
const store = useSessionStore();
const sessionId = store.session?.sessionId;
```

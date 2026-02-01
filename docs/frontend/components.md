# Frontend Components

The Career Intelligence Assistant frontend is built with React 18, TypeScript, and Tailwind CSS.

## Component Structure

```
frontend/src/components/
├── wizard/                    # Multi-step wizard flow
│   ├── WizardContainer.tsx    # Main wizard wrapper
│   ├── WizardProgress.tsx     # Step indicator
│   ├── UploadStep.tsx         # Step 1: Resume upload
│   ├── JobsStep.tsx           # Step 2: Add job descriptions
│   ├── AnalysisStep.tsx       # Step 3: Analysis progress
│   └── ExploreStep.tsx        # Step 4: View results
├── results/                   # Analysis result views
│   ├── FitScoreCard.tsx       # Fit score display
│   ├── SkillGapsList.tsx      # Missing skills list
│   ├── RecommendationsList.tsx # Improvement suggestions
│   ├── InterviewQuestions.tsx # Interview prep
│   └── MarketInsights.tsx     # Salary/market data
├── chat/                      # Real-time chat interface
│   ├── ChatContainer.tsx      # Chat wrapper
│   ├── ChatMessage.tsx        # Individual message
│   └── ChatInput.tsx          # Message input
└── ui/                        # Reusable UI components
    ├── Button.tsx             # Primary/secondary buttons
    ├── Card.tsx               # Content card
    ├── Input.tsx              # Form input
    ├── Modal.tsx              # Dialog modal
    ├── Progress.tsx           # Progress bar
    ├── Spinner.tsx            # Loading spinner
    └── Toast.tsx              # Notification toast
```

---

## Wizard Components

### WizardContainer

Main wrapper that manages wizard state and navigation.

**Location**: `frontend/src/components/wizard/WizardContainer.tsx`

```tsx
import { WizardContainer } from '@/components/wizard/WizardContainer';

function App() {
  return <WizardContainer />;
}
```

**Props**: None (uses Zustand stores internally)

**Responsibilities**:
- Renders current step component
- Manages navigation buttons
- Handles session initialization

---

### WizardProgress

Visual step indicator showing current progress.

**Location**: `frontend/src/components/wizard/WizardProgress.tsx`

```tsx
interface WizardProgressProps {
  currentStep: 1 | 2 | 3 | 4;
  steps: Array<{ label: string; icon: LucideIcon }>;
}
```

**Steps**:
1. Upload (FileUp icon)
2. Jobs (Briefcase icon)
3. Analysis (Sparkles icon)
4. Explore (Search icon)

---

### UploadStep (Step 1)

Resume upload interface supporting PDF, DOCX, and TXT files.

**Location**: `frontend/src/components/wizard/UploadStep.tsx`

**Features**:
- Drag-and-drop file upload
- File type validation (PDF, DOCX, TXT)
- File size validation (max 10MB)
- Upload progress indicator
- Parsed resume preview (skills, experience count)

**State Updates**:
- `sessionStore.setSession()` - Creates session
- `analysisStore.setResume()` - Stores parsed resume
- `wizardStore.setCanProceed(true)` - Enables next button

---

### JobsStep (Step 2)

Interface for adding job descriptions (up to 5).

**Location**: `frontend/src/components/wizard/JobsStep.tsx`

**Features**:
- Text area for pasting job postings
- Job cards showing parsed title/company
- Remove job functionality
- Job count indicator (X/5)

**State Updates**:
- `analysisStore.addJob()` - Adds parsed job
- `analysisStore.removeJob()` - Removes job
- `wizardStore.setCanProceed(true)` - When at least 1 job added

---

### AnalysisStep (Step 3)

Real-time analysis progress display.

**Location**: `frontend/src/components/wizard/AnalysisStep.tsx`

**Features**:
- Agent progress cards with status indicators
- Overall progress bar
- Estimated time remaining
- Error handling with retry option

**Agent Status Colors**:
- `pending` - Gray
- `running` - Blue (animated)
- `completed` - Green
- `failed` - Red

**WebSocket Integration**:
Uses `useAnalysisProgress` hook to receive real-time updates.

---

### ExploreStep (Step 4)

Results exploration interface with tabbed navigation.

**Location**: `frontend/src/components/wizard/ExploreStep.tsx`

**Tabs**:
| Tab | Component | Description |
|-----|-----------|-------------|
| Overview | `FitScoreCard` | Fit scores for all jobs |
| Skills | `SkillGapsList` | Matched/missing skills |
| Recommendations | `RecommendationsList` | Improvement suggestions |
| Interview | `InterviewQuestions` | Questions and STAR examples |
| Market | `MarketInsights` | Salary and demand data |

---

## Result Components

### FitScoreCard

Displays fit score as a circular gauge.

```tsx
interface FitScoreCardProps {
  score: number;          // 0-100
  jobTitle: string;
  company: string;
  matchedCount: number;
  missingCount: number;
}
```

**Visual**:
- Circular progress ring (green/yellow/red based on score)
- Score percentage in center
- Job title and company below
- Quick stats (matched/missing skills)

---

### SkillGapsList

Two-column list showing matched and missing skills.

```tsx
interface SkillGapsListProps {
  matchedSkills: Skill[];
  missingRequired: Skill[];
  missingNiceToHave: Skill[];
}
```

**Features**:
- Skills grouped by category
- Required vs nice-to-have distinction
- Proficiency level indicators

---

### RecommendationsList

Prioritized list of improvement suggestions.

```tsx
interface RecommendationsListProps {
  prioritySkills: SkillRecommendation[];
  resumeImprovements: string[];
  actionItems: ActionItem[];
}
```

**Sections**:
1. Priority Skills to Learn
2. Resume Improvements
3. Action Items (with priority badges)

---

### InterviewQuestions

Interview preparation content with expandable answers.

```tsx
interface InterviewQuestionsProps {
  technicalQuestions: Question[];
  behavioralQuestions: Question[];
  questionsToAsk: string[];
  starExamples: STARExample[];
}
```

**Features**:
- Expandable question cards
- STAR format answer templates
- Copy to clipboard functionality

---

### MarketInsights

Salary and market trend visualization.

```tsx
interface MarketInsightsProps {
  salaryRange: SalaryRange;
  demandTrend: 'growing' | 'stable' | 'declining';
  topCompanies: string[];
  relatedRoles: string[];
  skillDemand: SkillDemand[];
}
```

**Visualizations**:
- Salary range bar chart (Recharts)
- Demand trend indicator with icon
- Top companies list
- Related roles for career pathing

---

## UI Components

### Button

Primary action button with variants.

```tsx
interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  disabled?: boolean;
  children: React.ReactNode;
  onClick?: () => void;
}
```

**Usage**:
```tsx
<Button variant="primary" isLoading={isSubmitting}>
  Start Analysis
</Button>
```

---

### Card

Content container with optional header and footer.

```tsx
interface CardProps {
  title?: string;
  description?: string;
  footer?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}
```

---

### Progress

Progress bar component.

```tsx
interface ProgressProps {
  value: number;        // 0-100
  max?: number;         // Default 100
  showLabel?: boolean;
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'green' | 'red' | 'yellow';
}
```

---

## Styling Approach

### Tailwind CSS

All components use Tailwind utility classes:

```tsx
// Example component styling
<div className="flex flex-col gap-4 p-6 bg-white rounded-lg shadow-md">
  <h2 className="text-xl font-semibold text-gray-900">Title</h2>
  <p className="text-gray-600">Description</p>
</div>
```

### Design Tokens

Common values are defined in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: { /* blue shades */ },
        success: { /* green shades */ },
        warning: { /* yellow shades */ },
        error: { /* red shades */ },
      },
    },
  },
};
```

### Animation

Uses Framer Motion for transitions:

```tsx
import { motion } from 'framer-motion';

<motion.div
  initial={{ opacity: 0, y: 20 }}
  animate={{ opacity: 1, y: 0 }}
  exit={{ opacity: 0, y: -20 }}
>
  Content
</motion.div>
```

---

## Testing Components

Components are tested with Vitest and React Testing Library.

**Run tests**:
```bash
cd frontend
npm test                    # Run all tests
npm run test:ui             # Interactive UI
npm run test:coverage       # Coverage report
```

**Test file convention**: `ComponentName.test.tsx`

**Example test**:
```tsx
import { render, screen } from '@testing-library/react';
import { FitScoreCard } from './FitScoreCard';

describe('FitScoreCard', () => {
  it('displays the fit score', () => {
    render(
      <FitScoreCard
        score={85}
        jobTitle="Senior Engineer"
        company="TechCorp"
        matchedCount={10}
        missingCount={3}
      />
    );

    expect(screen.getByText('85%')).toBeInTheDocument();
  });
});
```

---

## Adding New Components

1. Create component file in appropriate directory
2. Export from directory `index.ts`
3. Add TypeScript interface for props
4. Use Tailwind for styling
5. Write tests in `*.test.tsx`
6. Document props in this file

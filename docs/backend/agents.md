# AI Agents Documentation

The Career Intelligence Assistant uses 7 specialized AI agents orchestrated via LlamaIndex workflows.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                             │
│                    (LlamaIndex Workflow)                         │
│   asyncio.Queue ←→ Agent Message Bus ←→ asyncio.Queue           │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Resume  │          │   JD    │          │  Skill  │
   │ Parser  │          │Analyzer │          │ Matcher │
   └────┬────┘          └────┬────┘          └────┬────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
   ┌─────────┐          ┌─────────┐          ┌─────────┐
   │ Recomm- │          │Interview│          │ Market  │
   │ endation│          │  Prep   │          │Insights │
   └─────────┘          └─────────┘          └─────────┘
```

## Execution Phases

| Phase | Agents | Execution | Purpose |
|-------|--------|-----------|---------|
| 1 | Resume Parser, JD Analyzer(s) | Parallel | Document parsing |
| 2 | Skill Matcher (per job) | Parallel | Fit calculation |
| 3 | Recommendation, Interview Prep, Market Insights | Parallel | Advanced analysis |

---

## Agent Details

### 1. Resume Parser Agent

**Location**: `backend/app/agents/resume_parser.py`

**Purpose**: Extracts structured data from resume documents including skills, experience, education, and certifications.

**Input Schema**:
```python
class ResumeParserInput(BaseModel):
    resume_text: str  # Raw text from PDF/DOCX
```

**Output Schema**:
```python
class ParsedResume(BaseModel):
    id: str                    # UUID
    skills: List[Skill]        # Extracted skills with levels
    experiences: List[Experience]
    education: List[Education]
    certifications: List[str]
    summary: str
    contact_redacted: bool     # True if PII was found
```

**Key Features**:
- PII redaction (SSN, email, phone, address)
- Graph-aware skill normalization via Neo4j
- Embedding-based skill deduplication
- Works for any job type (not tech-specific)

**Processing Steps**:
1. Redact PII from raw text
2. Send to LlamaIndex LLM for structured extraction
3. Normalize skills against existing Neo4j graph
4. Deduplicate using embedding similarity
5. Store parsed resume in Neo4j
6. Generate and store skill embeddings

---

### 2. JD Analyzer Agent

**Location**: `backend/app/agents/jd_analyzer.py`

**Purpose**: Parses job descriptions to extract requirements, required skills, and nice-to-have skills.

**Input Schema**:
```python
class JDAnalyzerInput(BaseModel):
    job_description: str  # Raw job posting text
```

**Output Schema**:
```python
class ParsedJobDescription(BaseModel):
    id: str
    title: str
    company: Optional[str]
    requirements: List[str]
    required_skills: List[Skill]
    nice_to_have_skills: List[Skill]
    experience_years_min: Optional[int]
    experience_years_max: Optional[int]
    education_requirements: List[str]
    responsibilities: List[str]
    culture_signals: List[str]
```

**Key Features**:
- Distinguishes required vs nice-to-have skills
- Extracts experience level requirements
- Identifies education requirements
- Detects company culture signals

---

### 3. Skill Matcher Agent

**Location**: `backend/app/agents/skill_matcher.py`

**Purpose**: Calculates fit score between resume and job description, identifies skill gaps.

**Input Schema**:
```python
class SkillMatcherInput(BaseModel):
    resume_id: str
    job_id: str
```

**Output Schema**:
```python
class SkillMatchResult(BaseModel):
    fit_score: float           # 0-100 percentage
    matched_skills: List[MatchedSkill]
    missing_required: List[Skill]
    missing_nice_to_have: List[Skill]
    experience_match: bool
    education_match: bool
```

**Matching Algorithm**:
1. **Exact match**: Direct skill name comparison
2. **Semantic match**: Embedding similarity (threshold: 0.75)
3. **Graph traversal**: Neo4j skill relationships
4. **Weighted scoring**: Required skills weighted higher than nice-to-have

---

### 4. Recommendation Agent

**Location**: `backend/app/agents/recommendation.py`

**Purpose**: Generates actionable improvement suggestions based on skill gaps.

**Output Schema**:
```python
class Recommendations(BaseModel):
    priority_skills: List[SkillRecommendation]
    learning_resources: List[Resource]
    resume_improvements: List[str]
    action_items: List[ActionItem]
```

**Recommendation Types**:
- Skill acquisition priorities
- Specific learning resources (courses, certifications)
- Resume wording improvements
- Experience positioning suggestions

---

### 5. Interview Prep Agent

**Location**: `backend/app/agents/interview_prep.py`

**Purpose**: Creates likely interview questions with STAR-format answer examples.

**Output Schema**:
```python
class InterviewPrep(BaseModel):
    technical_questions: List[Question]
    behavioral_questions: List[Question]
    questions_to_ask: List[str]
    star_examples: List[STARExample]
```

**Question Categories**:
- Technical questions based on required skills
- Behavioral questions based on job responsibilities
- Questions candidate should ask the interviewer
- STAR examples using candidate's experience

---

### 6. Market Insights Agent

**Location**: `backend/app/agents/market_insights.py`

**Purpose**: Provides salary ranges and career trend data.

**Output Schema**:
```python
class MarketInsights(BaseModel):
    salary_range: SalaryRange
    demand_trend: str          # "growing", "stable", "declining"
    top_companies_hiring: List[str]
    related_roles: List[str]
    skill_demand: List[SkillDemand]
```

**Data Sources**:
- LLM knowledge base
- Web scraping via Scrapy (when configured)

---

### 7. Chat Fit Agent

**Location**: `backend/app/agents/chat_fit.py`

**Purpose**: Conversational agent for answering questions about resume-job fit. Provides contextual, UK/EU market-focused career advice using session data.

**Input Schema**:
```python
class ChatFitInput(BaseModel):
    session_id: str          # Session containing resume and job data
    message: str             # User's question about the fit
    job_id: Optional[str]    # Specific job ID to focus on (optional)
```

**Output Schema**:
```python
class ChatFitOutput(BaseModel):
    response: str                    # AI response to the question
    suggested_questions: List[str]   # Follow-up questions user might ask
```

**Capabilities**:
- Answers questions about skill matches and gaps
- Provides interview preparation tips (UK competency-based format)
- Offers resume/CV improvement suggestions
- Compares fit across multiple job descriptions
- Gives UK/EU market-specific salary and career insights
- Suggests learning resources and certifications

**Key Features**:
- Uses session context (resume, jobs, match results)
- UK/EU market focus (GBP/EUR salaries, regional certifications)
- Prompt injection protection
- Generates contextual follow-up question suggestions
- Markdown-formatted responses with emoji highlights

---

## Base Agent Interface

All agents extend `BaseAgent` (located at `backend/app/agents/base_agent.py`):

```python
class BaseAgent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for the agent."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> Type[BaseModel]:
        """Pydantic model for input validation."""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> Type[BaseModel]:
        """Pydantic model for output validation."""
        pass

    @abstractmethod
    async def _execute(self, input_data: Any) -> Dict[str, Any]:
        """Main processing logic."""
        pass

    async def process(self, input_data: Any) -> AgentOutput:
        """Wraps _execute with error handling and timing."""
        pass

    async def report_progress(self, progress: int, step: str):
        """Broadcasts progress via WebSocket."""
        pass
```

## WebSocket Progress Updates

Agents broadcast real-time progress via WebSocket:

```json
{
  "type": "agent_progress",
  "agent_name": "resume_parser",
  "status": "running",
  "progress": 70,
  "current_step": "Processing extracted data"
}
```

**Status Values**: `pending`, `running`, `completed`, `failed`

## Error Handling

Agents return structured errors via `AgentOutput`:

```python
class AgentOutput(BaseModel):
    success: bool
    data: Dict[str, Any]
    errors: List[str]
    processing_time_ms: int
```

## Performance Benchmarks

| Agent | Typical Duration |
|-------|------------------|
| Resume Parser | 15-25 seconds |
| JD Analyzer | 10-15 seconds |
| Skill Matcher | 10-20 seconds per job |
| Recommendation | 10-15 seconds |
| Interview Prep | 10-15 seconds |
| Market Insights | 5-10 seconds |
| Chat Fit | 3-8 seconds per message |

## Adding a New Agent

1. Create `backend/app/agents/your_agent.py`
2. Extend `BaseAgent`
3. Define `input_schema` and `output_schema`
4. Implement `_execute()` method
5. Register in `backend/app/agents/__init__.py`
6. Add to workflow in `backend/app/workflows/analysis_workflow.py`

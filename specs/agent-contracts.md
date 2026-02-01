# Agent Contracts Specification

This document defines the interface contracts for all agents in the Career Intelligence Assistant system.

## Base Agent Contract

All agents must implement the following interface:

```python
class BaseAgentSpec(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique agent identifier."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of agent purpose."""
        pass

    @property
    @abstractmethod
    def input_schema(self) -> type[BaseModel]:
        """Pydantic model for input validation."""
        pass

    @property
    @abstractmethod
    def output_schema(self) -> type[BaseModel]:
        """Pydantic model for output validation."""
        pass

    @abstractmethod
    async def process(self, input: AgentInput) -> AgentOutput:
        """Process input and return validated output."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if agent is ready to process."""
        pass
```

---

## Agent 1: Resume Parser

### Purpose
Extract structured data from resume documents (PDF, DOCX, TXT).

### Input Schema
```python
class ResumeParserInput(AgentInput):
    session_id: str
    request_id: str
    document_content: str  # Raw text extracted from document
    document_type: Literal["pdf", "docx", "txt"]
    file_name: str
```

### Output Schema
```python
class ResumeParserOutput(AgentOutput):
    success: bool
    data: ParsedResume
    errors: List[str] = []
    processing_time_ms: int
    pii_detected: bool
    pii_redacted_fields: List[str] = []
```

### ParsedResume Structure
```python
class ParsedSkill(BaseModel):
    name: str
    category: SkillCategory  # programming, framework, tool, soft_skill, domain, certification, language
    level: SkillLevel  # beginner, intermediate, advanced, expert
    years_experience: Optional[float]
    source: Literal["explicit", "implicit"]  # explicit = listed in skills section, implicit = extracted from experience

class ParsedResume(BaseModel):
    id: str  # UUID
    skills: List[ParsedSkill]
    experiences: List[ParsedExperience]
    education: List[ParsedEducation]
    certifications: List[str] = []
    summary: Optional[str]
    contact_redacted: bool = True
```

### Behavior Requirements
1. MUST extract all skills mentioned in the resume (both explicit and implicit)
2. MUST categorize skills (programming, framework, tool, soft_skill, domain)
3. MUST estimate skill level based on context (beginner/intermediate/advanced/expert)
4. MUST extract work experience with company, title, duration
5. MUST extract education with degree, institution, year
6. MUST detect and redact PII before storing
7. MUST return structured JSON matching ParsedResume schema
8. MUST handle empty documents with appropriate error
9. MUST normalize skills using existing Neo4j graph context (LLM-driven normalization)
10. MUST mark skills as "explicit" (listed in skills section) or "implicit" (extracted from experience descriptions)
11. MUST use vector similarity fallback for skill deduplication when exact match not found

### Error Handling
- Empty document: Raise `ValueError("empty document")`
- Unparseable content: Return partial result with error message
- PII detection failure: Log warning, continue without redaction

---

## Agent 2: JD Analyzer

### Purpose
Parse job descriptions to extract requirements and qualifications.

### Input Schema
```python
class JDAnalyzerInput(AgentInput):
    session_id: str
    request_id: str
    job_text: str
    job_title: Optional[str]
    company: Optional[str]
```

### Output Schema
```python
class JDAnalyzerOutput(AgentOutput):
    success: bool
    data: ParsedJobDescription
    errors: List[str] = []
    processing_time_ms: int
```

### ParsedJobDescription Structure
```python
class ParsedJobDescription(BaseModel):
    id: str  # UUID
    title: str
    company: Optional[str]
    requirements: List[Requirement]
    required_skills: List[ParsedSkill]
    nice_to_have_skills: List[ParsedSkill]
    experience_years_min: Optional[int]
    experience_years_max: Optional[int]
    education_requirements: List[str] = []
    responsibilities: List[str] = []
    culture_signals: List[str] = []
```

### Behavior Requirements
1. MUST extract job title from content if not provided
2. MUST categorize requirements as must_have or nice_to_have
3. MUST extract minimum/maximum years of experience
4. MUST identify all required technical skills
5. MUST identify cultural fit indicators
6. MUST handle both structured and unstructured JD formats
7. MUST normalize skills using existing Neo4j graph context (LLM-driven normalization)
8. MUST mark skills as "explicit" (listed in requirements) or "implicit" (inferred from responsibilities)
9. MUST use vector similarity fallback for skill deduplication when exact match not found

---

## Agent 3: Skill Matcher

### Purpose
Compare resume skills against job requirements to calculate fit score.

### Input Schema
```python
class SkillMatcherInput(AgentInput):
    session_id: str
    request_id: str
    parsed_resume: ParsedResume
    parsed_job: ParsedJobDescription
```

### Output Schema
```python
class SkillMatcherOutput(AgentOutput):
    success: bool
    data: SkillMatchResult
    errors: List[str] = []
    processing_time_ms: int
```

### SkillMatchResult Structure
```python
class SkillMatchResult(BaseModel):
    job_id: str
    resume_id: str
    fit_score: float  # 0-100
    skill_match_score: float  # 0-100
    experience_match_score: float  # 0-100
    education_match_score: float  # 0-100
    matching_skills: List[SkillMatch]
    missing_skills: List[MissingSkill]
    transferable_skills: List[str] = []

class SkillMatch(BaseModel):
    skill_name: str
    resume_level: SkillLevel
    required_level: Optional[SkillLevel]
    match_quality: Literal["exact", "partial", "exceeds"]

class MissingSkill(BaseModel):
    skill_name: str
    importance: Literal["must_have", "nice_to_have"]
    difficulty_to_acquire: Literal["easy", "medium", "hard"]
```

### Behavior Requirements
1. MUST calculate overall fit score (0-100)
2. MUST identify exact skill matches
3. MUST identify missing must-have skills
4. MUST identify missing nice-to-have skills
5. MUST consider skill level when matching (advanced Python covers intermediate)
6. MUST identify transferable skills
7. MUST weight must-have skills higher than nice-to-have

### Scoring Algorithm
```
fit_score = (
    skill_match_score * 0.50 +
    experience_match_score * 0.35 +
    education_match_score * 0.15
)

skill_match_score = (
    matched_must_haves / total_must_haves * 0.70 +
    matched_nice_to_haves / total_nice_to_haves * 0.30
) * 100
```

---

## Agent 4: Recommendation

### Purpose
Generate actionable recommendations for improving resume and candidacy.

### Input Schema
```python
class RecommendationInput(AgentInput):
    session_id: str
    request_id: str
    parsed_resume: ParsedResume
    parsed_job: ParsedJobDescription
    skill_match: SkillMatchResult
```

### Output Schema
```python
class RecommendationOutput(AgentOutput):
    success: bool
    data: RecommendationResult
    errors: List[str] = []
    processing_time_ms: int
```

### RecommendationResult Structure
```python
class RecommendationResult(BaseModel):
    recommendations: List[Recommendation]
    priority_order: List[str]  # List of recommendation IDs
    estimated_improvement: float  # Potential fit score increase

class Recommendation(BaseModel):
    id: str  # UUID
    category: Literal["skill_gap", "resume_improvement", "experience_highlight", "certification", "networking"]
    priority: Literal["high", "medium", "low"]
    title: str
    description: str
    action_items: List[str]
    estimated_time: Optional[str]  # e.g., "2-4 weeks"
    resources: List[str] = []  # URLs or resource names
```

### Behavior Requirements
1. MUST generate at least 3 recommendations
2. MUST prioritize recommendations by impact on fit score
3. MUST include actionable steps for each recommendation
4. MUST categorize recommendations appropriately
5. MUST not recommend skills the candidate already has
6. MUST suggest highlighting existing relevant experience

---

## Agent 5: Interview Prep

### Purpose
Generate interview preparation materials based on resume and job match.

### Input Schema
```python
class InterviewPrepInput(AgentInput):
    session_id: str
    request_id: str
    parsed_resume: ParsedResume
    parsed_job: ParsedJobDescription
    skill_match: SkillMatchResult
```

### Output Schema
```python
class InterviewPrepOutput(AgentOutput):
    success: bool
    data: InterviewPrepResult
    errors: List[str] = []
    processing_time_ms: int
```

### InterviewPrepResult Structure
```python
class InterviewPrepResult(BaseModel):
    questions: List[InterviewQuestion]
    talking_points: List[str]
    weakness_responses: List[WeaknessResponse]
    questions_to_ask: List[str]

class InterviewQuestion(BaseModel):
    id: str
    question: str
    category: Literal["behavioral", "technical", "situational", "culture_fit"]
    difficulty: Literal["easy", "medium", "hard"]
    why_asked: str
    suggested_answer: str
    star_example: Optional[STARExample]
    related_experience: Optional[str]

class STARExample(BaseModel):
    situation: str
    task: str
    action: str
    result: str

class WeaknessResponse(BaseModel):
    weakness: str  # e.g., "Limited Kubernetes experience"
    honest_response: str
    mitigation: str
```

### Behavior Requirements
1. MUST generate at least 5 likely interview questions
2. MUST include mix of behavioral and technical questions
3. MUST base suggested answers on actual resume experience
4. MUST provide STAR examples using resume data
5. MUST address skill gaps with honest weakness responses
6. MUST generate questions for candidate to ask interviewer

---

## Agent 6: Market Insights

### Purpose
Provide market context for the target role using real-time web scraping and LLM analysis.

### Input Schema
```python
class MarketInsightsInput(AgentInput):
    session_id: str
    request_id: str
    parsed_job: ParsedJobDescription
    candidate_skills: List[str]
    location: Optional[str] = None
```

### Output Schema
```python
class MarketInsightsOutput(AgentOutput):
    success: bool
    data: MarketInsightsResult
    errors: List[str] = []
    processing_time_ms: int
```

### MarketInsightsResult Structure
```python
class MarketInsightsResult(BaseModel):
    salary_range: SalaryRange
    demand_trend: Literal["increasing", "stable", "decreasing"]
    top_skills_in_demand: List[str]
    career_paths: List[CareerPath]
    industry_insights: str
    competitive_landscape: str
    data_freshness: str  # e.g., "Based on real-time web scraping (Jan 2026)" or "Based on LLM market analysis"

class SalaryRange(BaseModel):
    min: int
    max: int
    median: int
    currency: str = "USD"
    location_adjusted: bool = False

class CareerPath(BaseModel):
    title: str
    typical_years_to_reach: int
    required_skills: List[str]
    salary_increase_percent: Optional[int]
```

### Behavior Requirements
1. MUST provide salary range for the role
2. MUST indicate job market demand trend
3. MUST list top skills in demand for the role
4. MUST suggest career progression paths
5. MUST acknowledge data source (real-time scraping vs LLM estimation)
6. SHOULD use Scrapy-based web scraping for real-time market data
7. SHOULD fall back to LLM general knowledge if scraping unavailable
8. SHOULD adjust for location if provided

---

## Graph-Aware Skill Normalization

### Purpose
Eliminate duplicate skill nodes and improve skill matching accuracy using LLM-driven normalization with Neo4j graph context.

### Normalization Flow
```
1. Query Neo4j → Get existing skill nodes (name, category) with 5-minute caching
2. Pass existing skills to LLM prompt as context
3. LLM extracts new skills AND maps them to existing nodes
4. Vector similarity (cosine) as fallback for edge cases (0.85 threshold)
```

### Skill Model
```python
class Skill(BaseModel):
    name: str  # Normalized name (e.g., "React" not "ReactJS")
    category: SkillCategory
    level: SkillLevel
    years_experience: Optional[float]
    source: Literal["explicit", "implicit"]
    # explicit = listed in skills section
    # implicit = extracted from experience/responsibilities descriptions
```

### Normalization Examples

| Input | Existing Graph | Output |
|-------|----------------|--------|
| "ReactJS" | "React (framework)" | Maps to "React" |
| "K8s" | Empty | Creates "Kubernetes" (industry standard) |
| "k8s" | "Kubernetes" | Maps to "Kubernetes" |
| "Built microservices using Docker" | "Docker" | Extracts & maps to "Docker" (source: implicit) |

### Performance Optimizations

| Step | Unoptimized | Optimized |
|------|-------------|-----------|
| Query existing skills | 20-50ms | ~1ms (5-min TTL cache) |
| LLM parse with context | 3-6s | 3-6s (unchanged) |
| Vector fallback (15 skills) | 1.5s (sequential) | ~200ms (parallel) |
| **Total Added Latency** | ~2s | **~200-400ms** |

### Implementation Files
| File | Function |
|------|----------|
| `neo4j_store.py` | `get_all_skills_cached()`, `find_similar_skills_by_embedding()` |
| `llamaindex_service.py` | Graph-context-aware prompts |
| `resume_parser.py` | `_deduplicate_with_embeddings()` |
| `jd_analyzer.py` | `_deduplicate_skills_with_embeddings()` |

---

## Message Bus Contract

### Message Format
```python
class AgentMessage(BaseModel):
    message_id: str  # UUID
    timestamp: datetime
    source_agent: str
    target_agent: Optional[str]  # None = broadcast
    message_type: Literal["request", "response", "error", "status"]
    payload: Dict[str, Any]
    correlation_id: str  # Links request to response
```

### Status Update Format
```python
class AgentStatus(BaseModel):
    agent_name: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: int  # 0-100
    current_step: Optional[str]
    error: Optional[str]
```

---

## Error Codes

| Code | Name | Description |
|------|------|-------------|
| E001 | EMPTY_INPUT | Input document is empty |
| E002 | PARSE_FAILED | Failed to parse document |
| E003 | LLM_ERROR | LLM API call failed |
| E004 | TIMEOUT | Agent processing timeout |
| E005 | VALIDATION_ERROR | Output schema validation failed |
| E006 | PII_DETECTION_FAILED | PII detection service unavailable |
| E007 | EMBEDDING_FAILED | Failed to generate embeddings |
| E008 | NEO4J_ERROR | Neo4j operation failed |

---

## Performance Requirements

| Agent | Max Processing Time | Target Processing Time |
|-------|---------------------|------------------------|
| Resume Parser | 30s | 10s |
| JD Analyzer | 20s | 5s |
| Skill Matcher | 10s | 3s |
| Recommendation | 20s | 8s |
| Interview Prep | 30s | 12s |
| Market Insights | 15s | 5s |

---

## Testing Requirements

Each agent must have:
1. Unit tests for input validation
2. Unit tests for output schema compliance
3. Unit tests for edge cases (empty input, malformed data)
4. Integration tests with mock LLM
5. Contract tests verifying interface compliance

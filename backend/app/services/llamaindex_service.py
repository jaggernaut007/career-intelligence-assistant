"""
LlamaIndex Service.

Provides unified access to LlamaIndex LLM, embeddings, and stores.
All LLM calls should go through this service - never call OpenAI directly.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Type, TypeVar

from pydantic import BaseModel

from app.config import get_settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LlamaIndexService:
    """
    Unified LlamaIndex service for the application.

    Wraps:
    - LlamaIndex OpenAI LLM
    - HuggingFace Embeddings

    Note: Graph data is stored directly in Neo4j via neo4j_store.py.
    Skill embeddings are stored on Skill nodes for semantic matching.
    """

    def __init__(self):
        """Initialize service (lazy loading)."""
        self._llm = None
        self._embed_model = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize all LlamaIndex components."""
        if self._initialized:
            return

        settings = get_settings()

        try:
            # Import LlamaIndex components
            from llama_index.core import Settings as LlamaSettings
            from llama_index.llms.openai import OpenAI as LlamaOpenAI
            from llama_index.embeddings.huggingface import HuggingFaceEmbedding

            # Initialize LLM with longer timeout for complex prompts
            logger.info(f"Initializing LlamaIndex LLM: {settings.openai_model}")
            self._llm = LlamaOpenAI(
                model=settings.openai_model,
                api_key=settings.openai_api_key,
                temperature=0.3,
                timeout=120.0,  # 2 minute timeout for complex prompts
                max_retries=3,  # Retry on transient failures
            )

            # Initialize embedding model
            logger.info(f"Initializing embedding model: {settings.embedding_model}")
            embed_kwargs = {
                "model_name": settings.embedding_model,
                "trust_remote_code": True,
            }
            # Add HuggingFace token if available
            if settings.hf_token:
                embed_kwargs["token"] = settings.hf_token
            self._embed_model = HuggingFaceEmbedding(**embed_kwargs)

            # Set global LlamaIndex settings
            LlamaSettings.llm = self._llm
            LlamaSettings.embed_model = self._embed_model

            self._initialized = True
            logger.info("LlamaIndex service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize LlamaIndex service: {e}")
            raise

    def _ensure_initialized(self) -> None:
        """Ensure service is initialized (sync check)."""
        if not self._initialized:
            raise RuntimeError(
                "LlamaIndexService not initialized. Call await initialize() first."
            )

    @property
    def llm(self):
        """Get the LLM instance."""
        self._ensure_initialized()
        return self._llm

    @property
    def embed_model(self):
        """Get the embedding model."""
        self._ensure_initialized()
        return self._embed_model

    # ========================================================================
    # LLM Methods
    # ========================================================================

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate completion using LlamaIndex LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        self._ensure_initialized()

        try:
            from llama_index.core.llms import ChatMessage, MessageRole

            messages = []
            if system_prompt:
                messages.append(ChatMessage(role=MessageRole.SYSTEM, content=system_prompt))
            messages.append(ChatMessage(role=MessageRole.USER, content=prompt))

            # Use async chat
            response = await self._llm.achat(messages, temperature=temperature)
            return response.message.content or ""

        except Exception as e:
            logger.error(f"LLM completion failed: {e}")
            raise

    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> Dict[str, Any]:
        """
        Generate JSON output from LLM.

        Args:
            prompt: User prompt requesting JSON
            system_prompt: Optional system prompt
            temperature: Sampling temperature

        Returns:
            Parsed JSON dict
        """
        # Add JSON instruction to system prompt
        json_system = (system_prompt or "") + "\n\nYou must respond with valid JSON only."

        response = await self.complete(prompt, json_system, temperature)

        # Parse JSON from response
        try:
            # Handle markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON response: {e}")
            # Try to extract JSON object
            import re
            match = re.search(r"\{.*\}", response, re.DOTALL)
            if match:
                return json.loads(match.group())
            raise ValueError(f"Invalid JSON response: {response[:200]}")

    async def complete_structured(
        self,
        prompt: str,
        output_schema: Type[T],
        system_prompt: Optional[str] = None,
        temperature: float = 0.3,
    ) -> T:
        """
        Generate structured output matching Pydantic schema.

        Args:
            prompt: User prompt
            output_schema: Pydantic model class
            system_prompt: Optional system prompt
            temperature: Sampling temperature

        Returns:
            Validated Pydantic model instance
        """
        # Get JSON schema from Pydantic model
        schema_json = json.dumps(output_schema.model_json_schema(), indent=2)

        structured_prompt = f"""{prompt}

Respond with a JSON object matching this schema:
{schema_json}
"""

        result = await self.complete_json(structured_prompt, system_prompt, temperature)
        return output_schema.model_validate(result)

    # ========================================================================
    # Embedding Methods
    # ========================================================================

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (768 dimensions)
        """
        self._ensure_initialized()

        try:
            # HuggingFace embedding is sync, wrap it
            embedding = self._embed_model.get_text_embedding(text)
            return embedding

        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        self._ensure_initialized()

        try:
            embeddings = self._embed_model.get_text_embedding_batch(texts)
            return embeddings

        except Exception as e:
            logger.error(f"Batch embedding generation failed: {e}")
            raise

    # ========================================================================
    # Resume/JD Parsing Methods
    # ========================================================================

    async def parse_resume(self, resume_text: str) -> Dict[str, Any]:
        """
        Parse resume text using LlamaIndex LLM with graph-aware skill normalization.

        Uses existing skills from Neo4j graph to normalize skill names and ensure
        consistent categorization across all resumes.

        Args:
            resume_text: Raw resume text

        Returns:
            Structured resume data with normalized skills
        """
        # Get existing skills from graph for normalization context
        from app.services.neo4j_store import get_neo4j_store
        existing_skills_context = ""
        try:
            neo4j_store = get_neo4j_store()
            existing_skills = await neo4j_store.get_all_skills_cached(limit=300)
            if existing_skills:
                skills_with_categories = [
                    f"{s['name']} ({s['category']})" if s.get('category') else s['name']
                    for s in existing_skills
                ]
                existing_skills_context = ", ".join(skills_with_categories)
        except Exception as e:
            logger.warning(f"Could not fetch existing skills for normalization: {e}")

        system_prompt = """You are an expert resume parser with skill normalization capabilities.

Your task is to analyze the resume text and extract:
- Skills with proficiency levels and categories (including implicit skills from experience descriptions)
- Work experiences with company names, titles, and durations
- Education history with degrees and institutions
- Certifications
- A brief professional summary

SKILL NORMALIZATION RULES:
1. If an extracted skill matches or is a variation of an existing skill in the database, USE THE EXISTING NAME exactly
   - Example: "ReactJS", "React.js", "react" → use "React" if it exists in database
   - Example: "K8s", "kube" → use "Kubernetes" if it exists in database
   - Example: "JS" → use "JavaScript" if it exists in database
2. If a skill is new (not in existing list), use standard industry naming (e.g., "Kubernetes" not "K8s")
3. Extract skills from EVERYWHERE - skills section, job descriptions, bullet points, project descriptions
4. Include implicit skills mentioned in context (e.g., "built REST APIs" → extract "REST APIs")

SKILL CATEGORIES:
- programming: Programming languages (Python, JavaScript, Go, etc.)
- framework: Libraries and frameworks (React, Django, Spring, etc.)
- tool: DevOps, platforms, tools (Docker, AWS, Git, etc.)
- soft_skill: Interpersonal skills (Leadership, Communication, etc.)
- domain: Industry/domain knowledge (Healthcare, Finance, Machine Learning, etc.)
- certification: Professional certifications (AWS Certified, PMP, etc.)
- language: Human languages (Spanish, Mandarin, etc.)

If a skill exists in the database, USE ITS EXISTING CATEGORY.

SKILL LEVELS:
- beginner: Less than 1 year experience
- intermediate: 1-3 years experience
- advanced: 3-5 years experience
- expert: 5+ years experience

SKILL SOURCE:
- "explicit": Skill was directly listed in a skills section
- "implicit": Skill was mentioned in experience descriptions, projects, or responsibilities"""

        # Build prompt with existing skills context
        existing_skills_section = ""
        if existing_skills_context:
            existing_skills_section = f"""
<existing_skills_in_database>
{existing_skills_context}
</existing_skills_in_database>

IMPORTANT: If you extract a skill that matches any variation of the above, use the EXACT name shown above.
"""

        prompt = f"""Parse this resume and extract ALL skills (both explicit and implicit):

<resume>
{resume_text}
</resume>
{existing_skills_section}
Return a JSON object with these fields:
- skills: Array of {{name, category, level, years_experience, source}}
  - source must be "explicit" or "implicit"
- experiences: Array of {{title, company, duration, description (single paragraph string, NOT a list of bullet points), skills_used}}
- education: Array of {{degree, institution, year, field_of_study}}
- certifications: Array of strings
- summary: Brief professional summary (1-2 sentences)

IMPORTANT:
1. 'level' must be one of: "beginner", "intermediate", "advanced", "expert"
2. 'source' must be one of: "explicit", "implicit"
3. Normalize skill names to match existing database skills when applicable
4. Extract skills mentioned in experience descriptions as implicit skills"""

        return await self.complete_json(prompt, system_prompt)

    async def parse_job_description(self, jd_text: str) -> Dict[str, Any]:
        """
        Parse job description text using LlamaIndex LLM with graph-aware skill normalization.

        Uses existing skills from Neo4j graph to normalize skill names and ensure
        JD skills match resume skills for accurate matching.

        Args:
            jd_text: Raw job description text

        Returns:
            Structured job description data with normalized skills
        """
        # Get existing skills from graph for normalization context
        from app.services.neo4j_store import get_neo4j_store
        existing_skills_context = ""
        try:
            neo4j_store = get_neo4j_store()
            existing_skills = await neo4j_store.get_all_skills_cached(limit=300)
            if existing_skills:
                skills_with_categories = [
                    f"{s['name']} ({s['category']})" if s.get('category') else s['name']
                    for s in existing_skills
                ]
                existing_skills_context = ", ".join(skills_with_categories)
        except Exception as e:
            logger.warning(f"Could not fetch existing skills for normalization: {e}")

        system_prompt = """You are an expert job description analyzer with skill normalization capabilities.

Your task is to analyze the job description and extract:
- Job title and company
- Required skills (must-have)
- Nice-to-have skills
- Experience requirements
- Education requirements
- Key responsibilities
- Culture signals (remote, fast-paced, etc.)

SKILL NORMALIZATION RULES:
1. If an extracted skill matches or is a variation of an existing skill in the database, USE THE EXISTING NAME exactly
   - Example: "ReactJS", "React.js", "react" → use "React" if it exists in database
   - Example: "K8s", "kube" → use "Kubernetes" if it exists in database
   - Example: "JS" → use "JavaScript" if it exists in database
2. If a skill is new (not in existing list), use standard industry naming
3. This ensures job skills match resume skills for accurate matching

SKILL CATEGORIES:
- programming: Programming languages (Python, JavaScript, Go, etc.)
- framework: Libraries and frameworks (React, Django, Spring, etc.)
- tool: DevOps, platforms, tools (Docker, AWS, Git, etc.)
- soft_skill: Interpersonal skills (Leadership, Communication, etc.)
- domain: Industry/domain knowledge (Healthcare, Finance, Machine Learning, etc.)
- certification: Professional certifications (AWS Certified, PMP, etc.)
- language: Human languages (Spanish, Mandarin, etc.)

If a skill exists in the database, USE ITS EXISTING CATEGORY.

SKILL LEVELS:
- beginner: Basic knowledge required
- intermediate: Working knowledge required
- advanced: Strong experience required
- expert: Deep expertise required"""

        # Build prompt with existing skills context
        existing_skills_section = ""
        if existing_skills_context:
            existing_skills_section = f"""
<existing_skills_in_database>
{existing_skills_context}
</existing_skills_in_database>

IMPORTANT: If you extract a skill that matches any variation of the above, use the EXACT name shown above.
"""

        prompt = f"""Parse this job description and extract structured data:

<job_description>
{jd_text}
</job_description>
{existing_skills_section}
Return a JSON object with these fields:
- title: Job title
- company: Company name (if mentioned)
- required_skills: Array of {{name, category, level}}
- nice_to_have_skills: Array of {{name, category, level}}
- experience_years_min: Minimum years required (integer or null)
- experience_years_max: Maximum years preferred (integer or null)
- education_requirements: Array of strings
- responsibilities: Array of responsibility descriptions
- culture_signals: Array of culture indicators (e.g., "remote-friendly", "fast-paced")

IMPORTANT:
1. 'level' must be one of: "beginner", "intermediate", "advanced", "expert"
2. Normalize skill names to match existing database skills when applicable"""

        return await self.complete_json(prompt, system_prompt)

    async def generate_recommendations(
        self,
        resume_summary: str = "",
        job_title: str = "",
        skill_gaps: List[str] = None,
        existing_skills: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate personalized recommendations using LlamaIndex LLM.

        Args:
            resume_summary: Resume summary text
            job_title: Target job title
            skill_gaps: List of missing skill names
            existing_skills: List of candidate's current skills

        Returns:
            List of recommendation dicts
        """
        skill_gaps = skill_gaps or []
        existing_skills = existing_skills or []

        prompt = f"""You are a career advisor. Generate personalized recommendations for a candidate.

CANDIDATE'S CURRENT SKILLS: {', '.join(existing_skills) if existing_skills else 'Not specified'}
RESUME SUMMARY: {resume_summary or 'Not provided'}

TARGET ROLE: {job_title}
SKILL GAPS: {', '.join(skill_gaps) if skill_gaps else 'None identified'}

Generate recommendations.
IMPORTANT RULES:
1. Generate EXACTLY 5 recommendations total. No more, no less.
2. For EACH recommendation, providing "action_items" is mandatory. You MUST provide at least 3 concrete, distinct action steps per recommendation.
3. If skill gaps exists, prioritize closing them (RecommendationCategory: skill_gap).
4. Include at least one "experience_highlight" recommendation specifically on how to REWORD/REFRAME existing resume bullets to match the target role. Do not suggest new projects here.
5. Include at least one certification or networking recommendation.
6. Make "estimated_time" realistic (e.g. "10-20 hours", "3-5 days").

Return a JSON array of recommendations:
[
  {{
    "title": "Learn [Skill]",
    "description": "Why this matters...",
    "action_items": [
      "Step 1: Do this...",
      "Step 2: Then do this...",
      "Step 3: Finally do this..."
    ],
    "estimated_time": "2-4 weeks",
    "resources": ["Resource 1", "Resource 2"],
    "priority": "high" 
  }}
]"""

        result = await self.complete_json(prompt)
        if isinstance(result, list):
            return result
        return result.get("recommendations", [])

    async def generate_interview_questions(
        self,
        job_title: str = "",
        company: str = "",
        required_skills: List[str] = None,
        responsibilities: List[str] = None,
        candidate_experience: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate interview questions using LlamaIndex LLM.

        Args:
            job_title: Target job title
            company: Company name
            required_skills: List of required skill names
            responsibilities: List of job responsibilities
            candidate_experience: List of candidate's experience summaries

        Returns:
            List of interview question dicts
        """
        required_skills = required_skills or []
        responsibilities = responsibilities or []
        candidate_experience = candidate_experience or []

        prompt = f"""You are an interview preparation expert. Generate likely interview questions for a candidate.

JOB TITLE: {job_title}
COMPANY: {company or 'Not specified'}

REQUIRED SKILLS: {', '.join(required_skills) if required_skills else 'Not specified'}

JOB RESPONSIBILITIES:
{chr(10).join('- ' + r for r in responsibilities[:5]) if responsibilities else 'Not specified'}

CANDIDATE'S EXPERIENCE:
{chr(10).join('- ' + e for e in candidate_experience[:3]) if candidate_experience else 'Not specified'}

Generate 8-12 likely interview questions across these categories:
1. Technical questions - testing knowledge of required skills
2. Behavioral questions - assessing past behavior and soft skills
3. Situational questions - hypothetical scenarios
4. Culture fit questions - alignment with company values

For each question, provide:
- The question itself
- The category (technical, behavioral, situational, culture_fit)
- Difficulty level (easy, medium, hard)
- Why this question is asked
- A suggested answer approach

Return a JSON array:
[
  {{
    "question": "Tell me about a time when...",
    "category": "behavioral",
    "difficulty": "medium",
    "why_asked": "Assesses problem-solving ability",
    "suggested_answer": "Use the STAR method to describe..."
  }}
]"""

        result = await self.complete_json(prompt)
        if isinstance(result, list):
            return result
        return result.get("questions", [])

    async def generate_full_interview_prep(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
        skill_gaps: List[str] = None,
    ) -> Dict[str, Any]:
        """Generate interview preparation materials."""
        skill_gaps = skill_gaps or []

        job_title = job_data.get("title", "the role")
        
        # Handle required_skills as list of dicts or list of strings
        raw_skills = job_data.get("required_skills", [])
        required_skills = []
        for s in raw_skills:
            if isinstance(s, dict):
                name = s.get("name", "")
                if name: required_skills.append(name)
            elif isinstance(s, str) and s:
                required_skills.append(s)
            elif hasattr(s, "name"): # Pydantic model
                required_skills.append(s.name)
        
        required_skills = required_skills[:5]

        # Handle experiences as list of dicts or objects
        raw_experiences = resume_data.get("experiences", [])
        experiences = []
        recent_exp = ""
        
        if raw_experiences:
            first_exp = raw_experiences[0]
            if isinstance(first_exp, dict):
                 recent_exp = first_exp.get('title', '')
            elif hasattr(first_exp, 'title'):
                 recent_exp = first_exp.title

        prompt = f"""Generate comprehensive interview prep for the {job_title} role in the UK/EU job market.

Candidate Experience: {recent_exp} (plus other experience)
Required Skills: {', '.join(required_skills)}
Identified Skill Gaps: {', '.join(skill_gaps[:3]) if skill_gaps else 'None'}

IMPORTANT: This is for the UK/EU market. UK interviews typically use competency-based questions with the STAR method.

Return a JSON object with this EXACT structure:
{{
  "behavioral_questions": [
    // Generate 3 competency-based questions (common in UK interviews). Ensure STAR examples are detailed.
    {{"question": "...", "why_asked": "...", "suggested_answer": "...", "star_example": {{"situation": "...", "task": "...", "action": "...", "result": "..."}}}}
  ],
  "technical_questions": [
    // Generate 3 questions.
    // IMPORTANT: If skill gaps are provided ({', '.join(skill_gaps[:3])}), generate at least one HARD question targeting them to test depth.
    {{"question": "...", "difficulty": "hard", "why_asked": "...", "suggested_answer": "..."}}
  ],
  "culture_fit_questions": [
    // UK employers often ask about values alignment and teamwork
    {{"question": "...", "why_asked": "...", "suggested_answer": "..."}}
  ],
  "weakness_responses": [
    // Provide responses for the skill gaps: {', '.join(skill_gaps[:3])}
    {{"weakness": "...", "honest_response": "...", "mitigation": "..."}}
  ],
  "questions_to_ask": [
    // Generate 3 strategic questions appropriate for UK/EU interviews:
    // 1. One about team structure and ways of working
    // 2. One about growth opportunities or learning & development
    // 3. One about company culture or hybrid/remote working policies
    "..."
  ],
  "talking_points": [
    // Generate 3 strong points that include QUANTIFIED impact (numbers, %, £) where possible.
    "Delivered X% improvement in...", "Managed £Y budget...", "Supported Z users across..."
  ]
}}
"""

        return await self.complete_json(prompt)

    async def generate_full_recommendations(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
        skill_gaps: List[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Generate recommendations for improving job fit."""
        skill_gaps = skill_gaps or []

        job_title = job_data.get("title", "the role")
        gap_names = [g.get("skill_name", "") for g in skill_gaps[:5] if g.get("skill_name")]

        # Extract resume summary and skills for context
        resume_summary = resume_data.get("summary", "")
        existing_skills = [s.get("name") for s in resume_data.get("skills", []) if isinstance(s, dict) and s.get("name")]
        
        prompt = f"""Generate personalized career recommendations/actions for a candidate targeting {job_title} in the UK/EU job market.

CANDIDATE'S CURRENT SKILLS: {', '.join(existing_skills[:10]) if existing_skills else 'Not specified'}...
CV SUMMARY: {resume_summary[:300] or 'Not provided'}
SKILL GAPS: {', '.join(gap_names) if gap_names else 'None identified'}

Generate individualized recommendations for the UK/EU market.
IMPORTANT RULES:
1. Generate EXACTLY 5 recommendations total. No more, no less.
2. For EACH recommendation, providing "action_items" is mandatory. You MUST provide at least 3 concrete, distinct action steps per recommendation.
3. If skill gaps exists, prioritize closing them (category: skill_gap).
4. Include at least one "resume_improvement" recommendation specifically on how to improve the CV content, formatting, or summary to match UK/EU employer expectations (e.g. "Add metrics", "Tailor for ATS systems").
5. Include at least one certification or networking recommendation - prefer UK/EU recognised certifications (e.g., CIPD, ACCA, Prince2, ITIL, BCS, AWS/Azure certs).
6. Make "estimated_time" realistic (e.g. "10-20 hours", "3-5 days").
7. For resources, include UK/EU platforms like FutureLearn, Open University, Coursera, LinkedIn Learning, and professional bodies.

Return a JSON array of recommendation objects:
[
  {{
    "title": "Learn [Skill]",
    "description": "Why this matters for UK/EU employers...",
    "category": "skill_gap", // One of: skill_gap, resume_improvement, experience_highlight, certification, networking
    "priority": "high", // One of: high, medium, low
    "action_items": [
      "Step 1: Do this...",
      "Step 2: Then do this...",
      "Step 3: Finally do this..."
    ],
    "estimated_time": "2-4 weeks",
    "resources": ["FutureLearn course on X", "LinkedIn Learning path for Y"]
  }}
]"""

        result = await self.complete_json(prompt)
        # Ensure result is a list
        if isinstance(result, list):
            return result
        # If wrapped in a dict (e.g. {"recommendations": [...]}), extract the list
        if isinstance(result, dict):
            for key in result:
                if isinstance(result[key], list):
                    return result[key]
        
        # Fallback
        return []


# ============================================================================
# Singleton Instance
# ============================================================================

_llamaindex_service: Optional[LlamaIndexService] = None


async def get_llamaindex_service() -> LlamaIndexService:
    """
    Get or create singleton LlamaIndex service.

    Returns:
        Initialized LlamaIndexService instance
    """
    global _llamaindex_service
    if _llamaindex_service is None:
        _llamaindex_service = LlamaIndexService()
        await _llamaindex_service.initialize()
    return _llamaindex_service


def get_llamaindex_service_sync() -> LlamaIndexService:
    """
    Get LlamaIndex service synchronously (must be already initialized).

    Returns:
        LlamaIndexService instance

    Raises:
        RuntimeError: If service not initialized
    """
    global _llamaindex_service
    if _llamaindex_service is None or not _llamaindex_service._initialized:
        raise RuntimeError(
            "LlamaIndexService not initialized. Use async get_llamaindex_service() first."
        )
    return _llamaindex_service

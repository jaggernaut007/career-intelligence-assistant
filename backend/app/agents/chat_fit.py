"""
Chat Fit Agent.

Conversational agent for answering questions about resume-job fit.
Uses Neo4j graph data and session match results to provide contextual answers.
"""

import logging
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from app.agents.base_agent import BaseAgent
from app.models.session import get_session_manager
from app.services.llamaindex_service import get_llamaindex_service
from app.services.neo4j_store import get_neo4j_store

logger = logging.getLogger(__name__)


class ChatFitInput(BaseModel):
    """Input schema for chat fit agent."""
    session_id: str = Field(..., description="Session ID containing resume and job data")
    message: str = Field(..., description="User's question about the fit")
    job_id: Optional[str] = Field(None, description="Specific job ID to focus on (optional)")


class ChatFitOutput(BaseModel):
    """Output schema for chat fit agent."""
    response: str = Field(..., description="AI response to the user's question")
    suggested_questions: List[str] = Field(
        default_factory=list,
        description="Follow-up questions the user might want to ask"
    )


class ChatFitAgent(BaseAgent):
    """
    Conversational agent for resume-job fit analysis.

    Answers questions about:
    - Skill matches and gaps
    - Experience alignment
    - Recommendations for improvement
    - Interview preparation tips
    - General career fit assessment
    """

    @property
    def name(self) -> str:
        return "chat_fit"

    @property
    def description(self) -> str:
        return "Conversational agent for answering questions about resume-job fit analysis"

    @property
    def input_schema(self) -> Type[BaseModel]:
        return ChatFitInput

    @property
    def output_schema(self) -> Type[BaseModel]:
        return ChatFitOutput

    async def health_check(self) -> bool:
        """Check if the agent is ready to process requests."""
        try:
            neo4j_store = get_neo4j_store()
            llamaindex_service = await get_llamaindex_service()
            return neo4j_store is not None and llamaindex_service is not None
        except Exception as e:
            logger.warning(f"Health check failed for {self.name}: {e}")
            return False

    def _build_context(
        self,
        resume_data: Dict[str, Any],
        job_data: Dict[str, Any],
        match_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Build context string from resume, job, and match data.

        Args:
            resume_data: Parsed resume data
            job_data: Parsed job description data
            match_data: Optional job match analysis results

        Returns:
            Formatted context string for LLM
        """
        # Extract resume info
        resume_summary = resume_data.get("summary", "No summary available")
        resume_skills = resume_data.get("skills", [])
        resume_experiences = resume_data.get("experiences", [])
        resume_education = resume_data.get("education", [])

        # Format skills with levels
        skill_list = []
        for s in resume_skills[:20]:  # Limit to top 20 skills
            if isinstance(s, dict):
                name = s.get("name", "")
                level = s.get("level", "")
                skill_list.append(f"{name} ({level})" if level else name)
            else:
                skill_list.append(str(s))

        # Format experiences
        exp_list = []
        for exp in resume_experiences[:5]:  # Limit to 5 experiences
            if isinstance(exp, dict):
                title = exp.get("title", "")
                company = exp.get("company", "")
                duration = exp.get("duration", "")
                exp_list.append(f"- {title} at {company} ({duration})")

        # Extract job info
        job_title = job_data.get("title", "Unknown Position")
        job_company = job_data.get("company", "")
        required_skills = job_data.get("required_skills", [])
        nice_to_have = job_data.get("nice_to_have_skills", [])
        exp_min = job_data.get("experience_years_min")
        exp_max = job_data.get("experience_years_max")

        # Format required skills
        req_skill_names = []
        for s in required_skills:
            if isinstance(s, dict):
                req_skill_names.append(s.get("name", ""))
            else:
                req_skill_names.append(str(s))

        # Format nice-to-have skills
        nice_skill_names = []
        for s in nice_to_have:
            if isinstance(s, dict):
                nice_skill_names.append(s.get("name", ""))
            else:
                nice_skill_names.append(str(s))

        # Build context
        context = f"""## CANDIDATE RESUME

**Summary:** {resume_summary}

**Skills:** {', '.join(skill_list) if skill_list else 'None listed'}

**Experience:**
{chr(10).join(exp_list) if exp_list else 'No experience listed'}

**Education:** {', '.join([e.get('degree', '') + ' from ' + e.get('institution', '') for e in resume_education[:3] if isinstance(e, dict)]) if resume_education else 'None listed'}

---

## TARGET JOB: {job_title}{' at ' + job_company if job_company else ''}

**Required Skills:** {', '.join(req_skill_names) if req_skill_names else 'None specified'}

**Nice-to-Have Skills:** {', '.join(nice_skill_names) if nice_skill_names else 'None specified'}

**Experience Required:** {f'{exp_min}-{exp_max} years' if exp_min and exp_max else f'{exp_min}+ years' if exp_min else 'Not specified'}
"""

        # Add match analysis if available
        if match_data:
            fit_score = match_data.get("fit_score", match_data.get("fitScore", 0))
            skill_score = match_data.get("skill_match_score", match_data.get("skillMatchScore", 0))
            exp_score = match_data.get("experience_match_score", match_data.get("experienceMatchScore", 0))
            edu_score = match_data.get("education_match_score", match_data.get("educationMatchScore", 0))

            matching_skills = match_data.get("matching_skills", match_data.get("matchingSkills", []))
            missing_skills = match_data.get("missing_skills", match_data.get("missingSkills", []))
            transferable = match_data.get("transferable_skills", match_data.get("transferableSkills", []))

            # Format matching skills
            matched_names = []
            for s in matching_skills:
                if isinstance(s, dict):
                    matched_names.append(s.get("skill_name", s.get("skillName", "")))
                else:
                    matched_names.append(str(s))

            # Format missing skills with importance
            gap_info = []
            for s in missing_skills:
                if isinstance(s, dict):
                    name = s.get("skill_name", s.get("skillName", ""))
                    importance = s.get("importance", "")
                    difficulty = s.get("difficulty_to_acquire", s.get("difficultyToAcquire", ""))
                    gap_info.append(f"{name} ({importance}, {difficulty} to learn)")
                else:
                    gap_info.append(str(s))

            context += f"""
---

## MATCH ANALYSIS

**Overall Fit Score:** {fit_score}%
- Skills Match: {skill_score}%
- Experience Match: {exp_score}%
- Education Match: {edu_score}%

**Matching Skills:** {', '.join(matched_names) if matched_names else 'None'}

**Skill Gaps:** {', '.join(gap_info) if gap_info else 'None - all required skills matched!'}

**Transferable Skills:** {', '.join(transferable) if transferable else 'None identified'}
"""

        return context

    def _get_suggested_questions(self, job_title: str, has_gaps: bool) -> List[str]:
        """
        Generate contextual suggested follow-up questions.

        Args:
            job_title: The target job title
            has_gaps: Whether there are skill gaps

        Returns:
            List of suggested questions
        """
        import random

        # Core questions based on context
        core_questions = []
        if has_gaps:
            core_questions.extend([
                "Which skill gap should I prioritize learning first?",
                "What's the fastest way to acquire the missing skills?",
                "Are there certifications that could help close these gaps?",
            ])
        else:
            core_questions.extend([
                "What makes me stand out for this role?",
                "How can I highlight my strengths in an interview?",
            ])

        # Interview & application questions
        interview_questions = [
            f"What interview questions should I prepare for {job_title}?",
            "How should I explain my career transitions in an interview?",
            "What should I emphasize in my cover letter?",
            "How can I tailor my resume for this specific role?",
        ]

        # Career strategy questions
        strategy_questions = [
            "What similar roles should I also consider applying for?",
            "Which of my jobs is the best fit and why?",
            "What career path could this role lead to?",
            "What skills would make me more competitive in this field?",
            "How does my experience compare to typical candidates?",
        ]

        # Job-specific questions (UK/EU focused)
        job_questions = [
            f"What do UK/EU employers typically look for in a {job_title}?",
            "What's the day-to-day like for this type of role?",
            "What salary range should I expect in the UK for this position?",
            "What UK certifications would strengthen my application?",
        ]

        # Combine and select diverse questions
        all_questions = core_questions + interview_questions + strategy_questions + job_questions

        # Always include at least one core question, then randomize the rest
        selected = core_questions[:1]
        remaining = [q for q in all_questions if q not in selected]
        random.shuffle(remaining)
        selected.extend(remaining[:3])

        return selected[:4]

    async def _execute(self, input_data: ChatFitInput) -> Dict[str, Any]:
        """
        Execute the chat agent to answer user's question.

        Args:
            input_data: Chat input with session_id, message, and optional job_id

        Returns:
            Dict with response and suggested_questions
        """
        await self.report_progress(10, "Loading session data")

        # Get session data
        session_manager = get_session_manager()
        session = session_manager.get_session(input_data.session_id)

        if session is None:
            raise ValueError("Session not found or expired")

        if session.parsed_resume is None:
            raise ValueError("No resume found in session. Please upload a resume first.")

        if not session.job_descriptions:
            raise ValueError("No job descriptions found. Please add at least one job description.")

        await self.report_progress(30, "Building context")

        # Get resume data
        resume_data = session.parsed_resume

        # Determine which job to focus on
        job_id = input_data.job_id
        if job_id and job_id in session.job_descriptions:
            job_data = session.job_descriptions[job_id]
        else:
            # Use first job if no specific job_id provided
            job_id = list(session.job_descriptions.keys())[0]
            job_data = session.job_descriptions[job_id]

        # Get match data if available
        match_data = None
        if session.job_matches:
            for match in session.job_matches:
                match_job_id = match.get("job_id", match.get("jobId", ""))
                if match_job_id == job_id:
                    match_data = match
                    break

        # Build context for LLM
        context = self._build_context(resume_data, job_data, match_data)

        await self.report_progress(50, "Generating response")

        # Create system prompt
        system_prompt = """You are an expert career advisor specialising in the UK and EU job market, helping a candidate understand their fit for a job position.

You have access to the candidate's resume, the job description, and match analysis results.

REGIONAL FOCUS - UK/EU Market:
- All salary discussions should be in GBP (£) for UK roles or EUR (€) for EU roles
- Reference UK/EU specific certifications (e.g., CIPD, ACCA, Prince2, ITIL, BCS)
- Consider UK/EU hiring practices and interview styles
- Mention relevant job boards: LinkedIn, Indeed UK, Totaljobs, Reed, Glassdoor UK, StepStone (EU)
- Reference key hiring hubs: London, Manchester, Birmingham, Edinburgh, Dublin, Amsterdam, Berlin, Paris

FOCUS AREAS - Always keep the conversation centered on:
1. **Resume/CV Analysis**: Skills, experiences, education, certifications, career progression (use "CV" terminology for UK)
2. **Job Fit**: How well the candidate matches each job, strengths and gaps
3. **Getting This Job**: Interview tips, how to present skills, addressing weaknesses (UK interview style tends to be competency-based)
4. **Finding Similar Jobs**: What other roles might suit them, related positions in UK/EU market
5. **Choosing Between Jobs**: Comparing multiple job options, which is the best fit and why
6. **Career Development**: Skills to learn, UK/EU recognised certifications to pursue, experience to gain
7. **Industry Insights**: What UK/EU employers look for, market trends in this region
8. **Application Strategy**: How to tailor CV, cover letter tips, UK/EU networking advice

If the user asks something unrelated to their career/resume/jobs, gently redirect:
- Acknowledge their question briefly
- Explain you're here to help with their job search and career fit
- Suggest a relevant topic they might want to explore instead

FORMATTING:
- Use markdown formatting for better readability
- Use **bold** for emphasis on key skills, scores, and important points
- Use bullet lists (-) for multiple items or steps
- Use emojis sparingly but effectively to highlight key points:
  - ✅ for matching skills or positive aspects
  - ❌ for gaps or missing requirements
  - 💡 for tips and suggestions
  - 🎯 for goals or priorities
  - 📈 for improvement opportunities
  - ⭐ for standout qualifications
- Keep paragraphs short and scannable

ALWAYS INCLUDE (add these proactively after answering the main question):

📋 **Recommendations** - At least 1-2 specific, actionable recommendations:
- Skills to develop or UK/EU recognised certifications to pursue
- How to strengthen their candidacy for UK/EU employers
- Resources or learning paths for skill gaps (mention UK/EU platforms like FutureLearn, Open University, Coursera)

🎤 **Interview Prep** - Relevant interview insights for UK/EU:
- Likely competency-based interview questions for this role
- How to discuss their experience using the STAR method (common in UK)
- Ways to address gaps or weaknesses positively

📊 **Market Insights** - UK/EU industry context when relevant:
- What UK/EU employers typically look for in this role
- How competitive their profile is
- Trends in the job market for these skills

GUIDELINES:
1. Answer questions directly and specifically based on the provided data
2. Reference specific skills, experiences, and scores when relevant
3. Be encouraging but honest about gaps and areas for improvement
4. Provide actionable advice - don't just describe, recommend next steps
5. Keep responses informative but scannable (use headers/bullets for longer responses)
6. Use the candidate's actual skills and experience in your answers
7. If asked about something not in the data, acknowledge what you don't know
8. End responses with a clear takeaway or action item when possible

Do NOT:
- Make up information not present in the context
- Give generic advice that doesn't reference the specific resume/job
- Be overly negative or discouraging
- Skip the recommendations/insights sections - they add value
- Overuse emojis (1-3 per response is ideal)
- Discuss topics completely unrelated to careers, jobs, or professional development"""

        # Create the prompt
        prompt = f"""{context}

---

## USER QUESTION

{input_data.message}

---

Please provide a helpful, specific answer based on the resume and job data above."""

        # Get LLM response
        llamaindex_service = await get_llamaindex_service()
        response = await llamaindex_service.complete(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=0.7,
        )

        await self.report_progress(90, "Preparing suggestions")

        # Determine if there are skill gaps
        has_gaps = False
        if match_data:
            missing = match_data.get("missing_skills", match_data.get("missingSkills", []))
            has_gaps = len(missing) > 0

        # Get suggested follow-up questions
        job_title = job_data.get("title", "this role")
        suggested_questions = self._get_suggested_questions(job_title, has_gaps)

        return {
            "response": response.strip(),
            "suggested_questions": suggested_questions,
        }

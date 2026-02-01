"""
Career Analysis Workflow using LlamaIndex Workflows.

This replaces the custom orchestrator + message bus with a proper
event-driven workflow engine with built-in parallel execution support.
"""

import logging
from typing import Optional, Any

from llama_index.core.workflow import (
    Workflow,
    step,
    Context,
    StopEvent,
)

from app.workflows.events import (
    StartAnalysisEvent,
    ResumeParseEvent,
    ResumeParseResultEvent,
    JDAnalyzeEvent,
    JDAnalyzeResultEvent,
    SkillMatchEvent,
    SkillMatchResultEvent,
    GenerateRecommendationsEvent,
    GenerateInterviewPrepEvent,
    GenerateMarketInsightsEvent,
    RecommendationResultEvent,
    InterviewPrepResultEvent,
    MarketInsightsResultEvent,
)

logger = logging.getLogger(__name__)


async def broadcast_workflow_progress(
    session_id: str,
    agent_name: str,
    status: str,
    progress: int = 0,
    current_step: str = None
) -> None:
    """
    Broadcast workflow progress to WebSocket clients.

    Args:
        session_id: Session ID
        agent_name: Agent or step name
        status: Current status (pending, running, completed, failed)
        progress: Progress percentage
        current_step: Description of current step
    """
    try:
        from app.api.websocket import broadcast_agent_progress
        await broadcast_agent_progress(
            session_id=session_id,
            agent_name=agent_name,
            status=status,
            progress=progress,
            current_step=current_step,
        )
    except Exception as e:
        logger.debug(f"Failed to broadcast workflow progress: {e}")


class CareerAnalysisWorkflow(Workflow):
    """
    Multi-agent workflow for career analysis.

    Flow:
    1. Parse resume + JDs in parallel (Phase 1)
    2. Match skills for each job in parallel (Phase 2)
    3. Generate recommendations, interview prep, market insights in parallel (Phase 3)

    Uses LlamaIndex Workflow features:
    - @step decorators with num_workers for parallel execution
    - ctx.store for shared state between steps
    - Typed events for inter-step communication
    - ctx.send_event() for dispatching multiple events
    """

    @step
    async def start(
        self,
        ctx: Context,
        ev: StartAnalysisEvent
    ) -> ResumeParseEvent | JDAnalyzeEvent | SkillMatchEvent | None:
        """Initialize workflow and dispatch Phase 1 parsing tasks or skip to Phase 2."""
        logger.info(f"Starting career analysis workflow for session {ev.session_id}")

        # Store session info in shared state using ctx.store
        await ctx.store.set("session_id", ev.session_id)
        await ctx.store.set("resume_id", ev.resume_id)
        await ctx.store.set("job_ids", ev.job_ids)
        await ctx.store.set("completed_steps", [])
        await ctx.store.set("parsed_jobs", {})
        await ctx.store.set("skill_matches", {})
        await ctx.store.set("all_skill_gaps", [])

        # Track what parsing is needed
        needs_resume_parsing = ev.resume_text is not None
        needs_jd_parsing = ev.job_texts is not None and len(ev.job_texts) > 0
        await ctx.store.set("needs_resume_parsing", needs_resume_parsing)
        await ctx.store.set("needs_jd_parsing", needs_jd_parsing)

        # Broadcast workflow start
        await broadcast_workflow_progress(
            ev.session_id, "workflow", "running", 5, "Starting analysis workflow"
        )

        first_event = None

        # If no parsing needed, skip directly to Phase 2 (skill matching)
        if not needs_resume_parsing and not needs_jd_parsing:
            logger.info("No parsing needed, skipping to Phase 2 (skill matching)")

            # Initialize skill matcher as pending
            await broadcast_workflow_progress(
                ev.session_id, "skill_matcher", "pending", 0, "Waiting to start"
            )

            # Dispatch skill matching events directly
            for job_id in ev.job_ids:
                match_event = SkillMatchEvent(
                    session_id=ev.session_id,
                    resume_id=ev.resume_id,
                    job_id=job_id
                )
                if first_event is None:
                    first_event = match_event
                else:
                    ctx.send_event(match_event)

            return first_event

        # Initialize agents as pending based on what's needed
        if needs_resume_parsing:
            await broadcast_workflow_progress(
                ev.session_id, "resume_parser", "pending", 0, "Waiting to start"
            )

        if needs_jd_parsing:
            await broadcast_workflow_progress(
                ev.session_id, "jd_analyzer", "pending", 0, "Waiting to start"
            )

        # Dispatch resume parsing
        if needs_resume_parsing:
            resume_event = ResumeParseEvent(
                resume_text=ev.resume_text,
                resume_id=ev.resume_id
            )
            if first_event is None:
                first_event = resume_event
            else:
                ctx.send_event(resume_event)

        # Dispatch JD parsing for each job
        if needs_jd_parsing:
            for job_id, jd_text in ev.job_texts.items():
                jd_event = JDAnalyzeEvent(
                    job_id=job_id,
                    jd_text=jd_text
                )
                if first_event is None:
                    first_event = jd_event
                else:
                    ctx.send_event(jd_event)

        logger.info(f"Dispatching parsing tasks (resume: {needs_resume_parsing}, JD: {needs_jd_parsing})")
        return first_event

    @step(num_workers=4)
    async def parse_resume(
        self,
        ctx: Context,
        ev: ResumeParseEvent
    ) -> ResumeParseResultEvent:
        """Parse resume and store in Neo4j."""
        session_id = await ctx.store.get("session_id")
        logger.info(f"Parsing resume {ev.resume_id}")

        from app.agents.resume_parser import ResumeParserAgent

        # Create agent with session_id for WebSocket updates
        agent = ResumeParserAgent(session_id=session_id)
        result = await agent.process(ev.resume_text)

        # Store in shared state
        await ctx.store.set("parsed_resume", result.data)

        return ResumeParseResultEvent(
            resume_id=ev.resume_id,
            parsed_resume=result.data
        )

    @step(num_workers=4)
    async def analyze_jd(
        self,
        ctx: Context,
        ev: JDAnalyzeEvent
    ) -> JDAnalyzeResultEvent:
        """Parse job description and store in Neo4j."""
        session_id = await ctx.store.get("session_id")
        logger.info(f"Analyzing job description {ev.job_id}")

        from app.agents.jd_analyzer import JDAnalyzerAgent

        # Create agent with session_id for WebSocket updates
        agent = JDAnalyzerAgent(session_id=session_id)
        result = await agent.process(ev.jd_text)

        # Thread-safe state update for parallel execution
        parsed_jobs = await ctx.store.get("parsed_jobs", default={})
        parsed_jobs[ev.job_id] = result.data
        await ctx.store.set("parsed_jobs", parsed_jobs)

        return JDAnalyzeResultEvent(
            job_id=ev.job_id,
            parsed_jd=result.data
        )

    @step
    async def collect_phase1(
        self,
        ctx: Context,
        ev: ResumeParseResultEvent | JDAnalyzeResultEvent
    ) -> SkillMatchEvent | None:
        """Collect Phase 1 results and trigger Phase 2."""
        session_id = await ctx.store.get("session_id")
        completed = await ctx.store.get("completed_steps", default=[])

        if isinstance(ev, ResumeParseResultEvent):
            completed.append("resume_parsed")
            logger.info("Resume parsing complete")
        else:
            completed.append(f"jd_parsed_{ev.job_id}")
            logger.info(f"JD parsing complete for {ev.job_id}")

        await ctx.store.set("completed_steps", completed)

        # Check if Phase 1 complete - only wait for what was dispatched
        job_ids = await ctx.store.get("job_ids", default=[])
        needs_resume_parsing = await ctx.store.get("needs_resume_parsing", default=False)
        needs_jd_parsing = await ctx.store.get("needs_jd_parsing", default=False)

        # Only wait for resume parsing if it was requested
        resume_done = (not needs_resume_parsing) or ("resume_parsed" in completed)

        # Only wait for JD parsing if it was requested
        jds_done = (not needs_jd_parsing) or all(f"jd_parsed_{jid}" in completed for jid in job_ids)

        if resume_done and jds_done:
            logger.info("Phase 1 complete, starting Phase 2")

            # Broadcast workflow progress
            await broadcast_workflow_progress(
                session_id, "workflow", "running", 35, "Phase 1 complete - Starting skill matching"
            )

            # Initialize skill matcher as pending
            await broadcast_workflow_progress(
                session_id, "skill_matcher", "pending", 0, "Waiting to start"
            )

            resume_id = await ctx.store.get("resume_id")

            # Dispatch skill matching for each job
            first_event = None
            for job_id in job_ids:
                match_event = SkillMatchEvent(
                    session_id=session_id,
                    resume_id=resume_id,
                    job_id=job_id
                )
                if first_event is None:
                    first_event = match_event
                else:
                    ctx.send_event(match_event)

            return first_event

        return None

    @step(num_workers=5)
    async def match_skills(
        self,
        ctx: Context,
        ev: SkillMatchEvent
    ) -> SkillMatchResultEvent:
        """Match skills between resume and job."""
        session_id = await ctx.store.get("session_id")
        logger.info(f"Matching skills for job {ev.job_id}")

        from app.agents.skill_matcher import SkillMatcherAgent

        # Create agent with session_id for WebSocket updates
        agent = SkillMatcherAgent(session_id=session_id)
        result = await agent.process({
            "session_id": ev.session_id,
            "resume_id": ev.resume_id,
            "job_id": ev.job_id
        })

        # Store match result in shared state
        skill_matches = await ctx.store.get("skill_matches", default={})
        skill_matches[ev.job_id] = result.data
        await ctx.store.set("skill_matches", skill_matches)

        # Aggregate skill gaps
        all_gaps = await ctx.store.get("all_skill_gaps", default=[])
        for skill in result.data.get("missing_skills", []):
            skill_name = skill.get("skill_name", "") if isinstance(skill, dict) else str(skill)
            if skill_name and skill_name not in all_gaps:
                all_gaps.append(skill_name)
        await ctx.store.set("all_skill_gaps", all_gaps)

        return SkillMatchResultEvent(
            job_id=ev.job_id,
            match_result=result.data
        )

    @step
    async def collect_phase2(
        self,
        ctx: Context,
        ev: SkillMatchResultEvent
    ) -> GenerateRecommendationsEvent | GenerateInterviewPrepEvent | GenerateMarketInsightsEvent | None:
        """Collect Phase 2 results and trigger Phase 3."""
        session_id = await ctx.store.get("session_id")
        completed = await ctx.store.get("completed_steps", default=[])
        completed.append(f"matched_{ev.job_id}")
        await ctx.store.set("completed_steps", completed)

        logger.info(f"Skill matching complete for {ev.job_id}")

        # Check if all jobs matched
        job_ids = await ctx.store.get("job_ids", default=[])
        all_matched = all(f"matched_{jid}" in completed for jid in job_ids)

        if all_matched:
            logger.info("Phase 2 complete, starting Phase 3")

            # Broadcast workflow progress
            await broadcast_workflow_progress(
                session_id, "workflow", "running", 60, "Phase 2 complete - Generating insights"
            )

            # Initialize Phase 3 agents as pending
            await broadcast_workflow_progress(
                session_id, "recommendation", "pending", 0, "Waiting to start"
            )
            await broadcast_workflow_progress(
                session_id, "interview_prep", "pending", 0, "Waiting to start"
            )
            await broadcast_workflow_progress(
                session_id, "market_insights", "pending", 0, "Waiting to start"
            )

            skill_gaps = await ctx.store.get("all_skill_gaps", default=[])

            # Get job title for market insights
            skill_matches = await ctx.store.get("skill_matches", default={})
            first_job = skill_matches.get(job_ids[0], {}) if job_ids else {}
            job_title = first_job.get("job_title", "Software Engineer")

            # Return first event, send the rest
            rec_event = GenerateRecommendationsEvent(
                session_id=session_id,
                skill_gaps=skill_gaps
            )
            ctx.send_event(GenerateInterviewPrepEvent(
                session_id=session_id,
                skill_gaps=skill_gaps
            ))
            ctx.send_event(GenerateMarketInsightsEvent(
                session_id=session_id,
                job_title=job_title
            ))

            return rec_event

        return None

    @step(num_workers=3)
    async def generate_recommendations(
        self,
        ctx: Context,
        ev: GenerateRecommendationsEvent
    ) -> RecommendationResultEvent:
        """Generate improvement recommendations."""
        session_id = await ctx.store.get("session_id")
        logger.info("Generating recommendations")

        from app.agents.recommendation import RecommendationAgent

        resume_id = await ctx.store.get("resume_id")
        job_ids = await ctx.store.get("job_ids", default=[])

        # Create agent with session_id for WebSocket updates
        agent = RecommendationAgent(session_id=session_id)
        result = await agent.process({
            "session_id": ev.session_id,
            "resume_id": resume_id,
            "job_id": job_ids[0] if job_ids else None,
            "skill_gaps": ev.skill_gaps
        })

        await ctx.store.set("recommendations", result.data)
        return RecommendationResultEvent(recommendations=result.data)

    @step(num_workers=3)
    async def generate_interview_prep(
        self,
        ctx: Context,
        ev: GenerateInterviewPrepEvent
    ) -> InterviewPrepResultEvent:
        """Generate interview preparation materials."""
        session_id = await ctx.store.get("session_id")
        logger.info("Generating interview prep")

        from app.agents.interview_prep import InterviewPrepAgent

        resume_id = await ctx.store.get("resume_id")
        job_ids = await ctx.store.get("job_ids", default=[])

        # Create agent with session_id for WebSocket updates
        agent = InterviewPrepAgent(session_id=session_id)
        result = await agent.process({
            "session_id": ev.session_id,
            "resume_id": resume_id,
            "job_id": job_ids[0] if job_ids else None,
            "skill_gaps": ev.skill_gaps
        })

        await ctx.store.set("interview_prep", result.data)
        return InterviewPrepResultEvent(interview_prep=result.data)

    @step(num_workers=3)
    async def generate_market_insights(
        self,
        ctx: Context,
        ev: GenerateMarketInsightsEvent
    ) -> MarketInsightsResultEvent:
        """Generate market insights."""
        session_id = await ctx.store.get("session_id")
        logger.info("Generating market insights")

        from app.agents.market_insights import MarketInsightsAgent

        job_ids = await ctx.store.get("job_ids", default=[])

        # Create agent with session_id for WebSocket updates
        agent = MarketInsightsAgent(session_id=session_id)
        result = await agent.process({
            "session_id": ev.session_id,
            "job_id": job_ids[0] if job_ids else None,
            "job_title": ev.job_title
        })

        await ctx.store.set("market_insights", result.data)
        return MarketInsightsResultEvent(market_insights=result.data)

    @step
    async def finalize(
        self,
        ctx: Context,
        ev: RecommendationResultEvent | InterviewPrepResultEvent | MarketInsightsResultEvent
    ) -> StopEvent | None:
        """Collect Phase 3 results and finalize."""
        session_id = await ctx.store.get("session_id")
        completed = await ctx.store.get("completed_steps", default=[])

        if isinstance(ev, RecommendationResultEvent):
            completed.append("recommendations")
            logger.info("Recommendations generated")
        elif isinstance(ev, InterviewPrepResultEvent):
            completed.append("interview_prep")
            logger.info("Interview prep generated")
        else:
            completed.append("market_insights")
            logger.info("Market insights generated")

        await ctx.store.set("completed_steps", completed)

        # Check if all Phase 3 complete
        phase3_done = all(step in completed for step in [
            "recommendations", "interview_prep", "market_insights"
        ])

        if phase3_done:
            logger.info("Phase 3 complete, finalizing workflow")

            # Broadcast workflow completion
            await broadcast_workflow_progress(
                session_id, "workflow", "completed", 100, "Analysis complete"
            )

            # Build final result from shared state
            resume_id = await ctx.store.get("resume_id")
            skill_matches = await ctx.store.get("skill_matches", default={})
            recommendations = await ctx.store.get("recommendations")
            interview_prep = await ctx.store.get("interview_prep")
            market_insights = await ctx.store.get("market_insights")

            return StopEvent(result={
                "success": True,
                "session_id": session_id,
                "resume_id": resume_id,
                "job_matches": list(skill_matches.values()),
                "recommendations": recommendations,
                "interview_prep": interview_prep,
                "market_insights": market_insights,
            })

        return None


# Factory function for creating workflow instances
def get_workflow() -> CareerAnalysisWorkflow:
    """Create a new workflow instance."""
    return CareerAnalysisWorkflow(timeout=600)  # 10 minute timeout

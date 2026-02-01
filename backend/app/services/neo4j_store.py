"""
Neo4j Store Service.

Handles graph and vector operations using Neo4j.
Uses LlamaIndex's Neo4j integrations for seamless RAG support.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from neo4j import AsyncGraphDatabase, GraphDatabase

from app.config import get_settings
from app.models import ParsedJobDescription, ParsedResume

logger = logging.getLogger(__name__)


class Neo4jStore:
    """Neo4j graph and vector store operations."""

    # Connection pool configuration for better concurrent performance
    MAX_CONNECTION_POOL_SIZE = 50  # Maximum connections in pool
    CONNECTION_ACQUISITION_TIMEOUT = 60  # Seconds to wait for connection
    MAX_CONNECTION_LIFETIME = 3600  # Max lifetime of connection (1 hour)
    CONNECTION_TIMEOUT = 30  # Timeout for establishing connection

    def __init__(self):
        """Initialize Neo4j connection."""
        self._driver = None
        self._async_driver = None
        self._connected = False

    def _get_driver(self):
        """Get or create Neo4j driver with connection pooling."""
        if self._driver is None:
            try:
                settings = get_settings()
                self._driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_username, settings.neo4j_password),
                    max_connection_pool_size=self.MAX_CONNECTION_POOL_SIZE,
                    connection_acquisition_timeout=self.CONNECTION_ACQUISITION_TIMEOUT,
                    max_connection_lifetime=self.MAX_CONNECTION_LIFETIME,
                    connection_timeout=self.CONNECTION_TIMEOUT,
                )
                self._driver.verify_connectivity()
                self._connected = True
                logger.info(f"Connected to Neo4j (pool_size={self.MAX_CONNECTION_POOL_SIZE})")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                self._connected = False
                raise
        return self._driver

    async def _get_async_driver(self):
        """Get or create async Neo4j driver with connection pooling."""
        if self._async_driver is None:
            try:
                settings = get_settings()
                self._async_driver = AsyncGraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_username, settings.neo4j_password),
                    max_connection_pool_size=self.MAX_CONNECTION_POOL_SIZE,
                    connection_acquisition_timeout=self.CONNECTION_ACQUISITION_TIMEOUT,
                    max_connection_lifetime=self.MAX_CONNECTION_LIFETIME,
                    connection_timeout=self.CONNECTION_TIMEOUT,
                )
                await self._async_driver.verify_connectivity()
                self._connected = True
                logger.info(f"Connected to Neo4j async (pool_size={self.MAX_CONNECTION_POOL_SIZE})")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")
                self._connected = False
                raise
        return self._async_driver

    def is_connected(self) -> bool:
        """Check if connected to Neo4j."""
        if self._driver is None:
            return False
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    def close(self) -> None:
        """Close Neo4j connection."""
        if self._driver:
            self._driver.close()
            self._driver = None
        if self._async_driver:
            # Note: async close needs to be awaited
            self._async_driver = None
        self._connected = False
        logger.info("Neo4j connection closed")

    # ========================================================================
    # Resume Operations
    # ========================================================================

    async def save_resume(self, resume: ParsedResume) -> bool:
        """
        Save parsed resume to Neo4j.

        Creates Resume node and related Skill, Experience, Education nodes.
        """
        driver = await self._get_async_driver()

        query = """
        MERGE (r:Resume {id: $id})
        SET r.summary = $summary,
            r.contact_redacted = $contact_redacted,
            r.updated_at = datetime()
        WITH r

        // Create skill nodes and relationships
        UNWIND $skills AS skill
        MERGE (s:Skill {name: skill.name})
        SET s.category = skill.category
        MERGE (r)-[hs:HAS_SKILL]->(s)
        SET hs.level = skill.level,
            hs.years_experience = skill.years_experience

        WITH r

        // Create experience nodes
        UNWIND $experiences AS exp
        MERGE (e:Experience {
            resume_id: $id,
            title: exp.title,
            company: exp.company
        })
        SET e.duration = exp.duration,
            e.duration_months = exp.duration_months,
            e.description = exp.description
        MERGE (r)-[:HAS_EXPERIENCE]->(e)

        WITH r

        // Create education nodes
        UNWIND $education AS edu
        MERGE (ed:Education {
            resume_id: $id,
            degree: edu.degree,
            institution: edu.institution
        })
        SET ed.year = edu.year,
            ed.gpa = edu.gpa,
            ed.field_of_study = edu.field_of_study
        MERGE (r)-[:HAS_EDUCATION]->(ed)

        RETURN r
        """

        try:
            async with driver.session() as session:
                result = await session.run(
                    query,
                    id=resume.id,
                    summary=resume.summary,
                    contact_redacted=resume.contact_redacted,
                    skills=[s.model_dump() for s in resume.skills],
                    experiences=[e.model_dump() for e in resume.experiences],
                    education=[e.model_dump() for e in resume.education]
                )
                await result.consume()
                return True

        except Exception as e:
            logger.error(f"Error saving resume: {e}")
            raise

    async def get_resume(self, resume_id: str) -> Optional[ParsedResume]:
        """Get resume by ID."""
        driver = await self._get_async_driver()

        query = """
        MATCH (r:Resume {id: $id})
        OPTIONAL MATCH (r)-[hs:HAS_SKILL]->(s:Skill)
        OPTIONAL MATCH (r)-[:HAS_EXPERIENCE]->(e:Experience)
        OPTIONAL MATCH (r)-[:HAS_EDUCATION]->(ed:Education)
        RETURN r,
               collect(DISTINCT {name: s.name, category: s.category, level: hs.level, years_experience: hs.years_experience}) as skills,
               collect(DISTINCT {title: e.title, company: e.company, duration: e.duration, duration_months: e.duration_months, description: e.description}) as experiences,
               collect(DISTINCT {degree: ed.degree, institution: ed.institution, year: ed.year, gpa: ed.gpa, field_of_study: ed.field_of_study}) as education
        """

        try:
            async with driver.session() as session:
                result = await session.run(query, id=resume_id)
                record = await result.single()

                if not record:
                    return None

                r = record["r"]

                # Reconstruct skills from query results
                from app.models import Skill, SkillCategory, SkillLevel, Experience, Education

                skills = []
                for skill_data in record["skills"]:
                    if skill_data.get("name"):
                        try:
                            category = SkillCategory(skill_data.get("category", "domain"))
                        except ValueError:
                            category = SkillCategory.DOMAIN
                        try:
                            level = SkillLevel(skill_data.get("level", "intermediate"))
                        except ValueError:
                            level = SkillLevel.INTERMEDIATE

                        skills.append(Skill(
                            name=skill_data["name"],
                            category=category,
                            level=level,
                            years_experience=skill_data.get("years_experience")
                        ))

                # Reconstruct experiences from query results
                experiences = []
                for exp_data in record["experiences"]:
                    if exp_data.get("title") and exp_data.get("company"):
                        experiences.append(Experience(
                            title=exp_data["title"],
                            company=exp_data["company"],
                            duration=exp_data.get("duration", "Not specified"),
                            duration_months=exp_data.get("duration_months"),
                            description=exp_data.get("description", ""),
                            skills_used=[]
                        ))

                # Reconstruct education from query results
                education = []
                for edu_data in record["education"]:
                    if edu_data.get("degree") and edu_data.get("institution"):
                        education.append(Education(
                            degree=edu_data["degree"],
                            institution=edu_data["institution"],
                            year=edu_data.get("year"),
                            gpa=edu_data.get("gpa"),
                            field_of_study=edu_data.get("field_of_study")
                        ))

                return ParsedResume(
                    id=r["id"],
                    summary=r.get("summary"),
                    contact_redacted=r.get("contact_redacted", True),
                    skills=skills,
                    experiences=experiences,
                    education=education,
                    certifications=[]
                )

        except Exception as e:
            logger.error(f"Error getting resume: {e}")
            return None

    # ========================================================================
    # Job Description Operations
    # ========================================================================

    async def save_job_description(self, jd: ParsedJobDescription) -> bool:
        """Save parsed job description to Neo4j."""
        driver = await self._get_async_driver()

        query = """
        MERGE (j:JobDescription {id: $id})
        SET j.title = $title,
            j.company = $company,
            j.experience_years_min = $experience_years_min,
            j.experience_years_max = $experience_years_max,
            j.updated_at = datetime()

        WITH j

        // Create required skill relationships
        UNWIND $required_skills AS skill
        MERGE (s:Skill {name: skill.name})
        SET s.category = skill.category
        MERGE (j)-[req:REQUIRES_SKILL {type: 'required'}]->(s)
        SET req.level = skill.level

        WITH j

        // Create nice-to-have skill relationships
        UNWIND $nice_to_have_skills AS skill
        MERGE (s:Skill {name: skill.name})
        SET s.category = skill.category
        MERGE (j)-[nth:REQUIRES_SKILL {type: 'nice_to_have'}]->(s)
        SET nth.level = skill.level

        RETURN j
        """

        try:
            async with driver.session() as session:
                result = await session.run(
                    query,
                    id=jd.id,
                    title=jd.title,
                    company=jd.company,
                    experience_years_min=jd.experience_years_min,
                    experience_years_max=jd.experience_years_max,
                    required_skills=[s.model_dump() for s in jd.required_skills],
                    nice_to_have_skills=[s.model_dump() for s in jd.nice_to_have_skills]
                )
                await result.consume()
                return True

        except Exception as e:
            logger.error(f"Error saving job description: {e}")
            raise

    async def get_job_description(self, job_id: str) -> Optional[ParsedJobDescription]:
        """Get job description by ID."""
        driver = await self._get_async_driver()

        query = """
        MATCH (j:JobDescription {id: $id})
        OPTIONAL MATCH (j)-[req:REQUIRES_SKILL]->(s:Skill)
        RETURN j, collect({name: s.name, category: s.category, type: req.type, level: req.level}) as skills
        """

        try:
            async with driver.session() as session:
                result = await session.run(query, id=job_id)
                record = await result.single()

                if not record:
                    return None

                j = record["j"]

                # Reconstruct skills from query results
                from app.models import Skill, SkillCategory, SkillLevel

                required_skills = []
                nice_to_have_skills = []

                for skill_data in record["skills"]:
                    if skill_data.get("name"):
                        try:
                            category = SkillCategory(skill_data.get("category", "domain"))
                        except ValueError:
                            category = SkillCategory.DOMAIN
                        try:
                            level = SkillLevel(skill_data.get("level", "intermediate"))
                        except ValueError:
                            level = SkillLevel.INTERMEDIATE

                        skill = Skill(
                            name=skill_data["name"],
                            category=category,
                            level=level,
                            years_experience=None
                        )

                        # Categorize by requirement type
                        if skill_data.get("type") == "required":
                            required_skills.append(skill)
                        else:
                            nice_to_have_skills.append(skill)

                return ParsedJobDescription(
                    id=j["id"],
                    title=j["title"],
                    company=j.get("company"),
                    requirements=[],
                    required_skills=required_skills,
                    nice_to_have_skills=nice_to_have_skills,
                    experience_years_min=j.get("experience_years_min"),
                    experience_years_max=j.get("experience_years_max"),
                    education_requirements=[],
                    responsibilities=[],
                    culture_signals=[]
                )

        except Exception as e:
            logger.error(f"Error getting job description: {e}")
            return None

    # ========================================================================
    # Skill Operations
    # ========================================================================

    async def create_or_merge_skill(self, name: str, category: str) -> bool:
        """Create or merge a skill node."""
        driver = await self._get_async_driver()

        query = """
        MERGE (s:Skill {name: $name})
        SET s.category = $category
        RETURN s
        """

        try:
            async with driver.session() as session:
                await session.run(query, name=name, category=category)
                return True

        except Exception as e:
            logger.error(f"Error creating skill: {e}")
            raise

    async def count_skill_nodes(self, name: str) -> int:
        """Count skill nodes with given name."""
        driver = await self._get_async_driver()

        query = "MATCH (s:Skill {name: $name}) RETURN count(s) as count"

        try:
            async with driver.session() as session:
                result = await session.run(query, name=name)
                record = await result.single()
                return record["count"] if record else 0

        except Exception as e:
            logger.error(f"Error counting skills: {e}")
            return 0

    async def get_all_skills(self, limit: int = 500) -> List[Dict[str, Any]]:
        """
        Get all unique skill nodes for LLM context.

        Returns list of skills with name and category for use in
        LLM prompts to enable graph-aware skill normalization.
        """
        driver = await self._get_async_driver()

        query = """
        MATCH (s:Skill)
        WHERE s.name IS NOT NULL
        RETURN s.name AS name, s.category AS category
        ORDER BY s.name
        LIMIT $limit
        """

        try:
            async with driver.session() as session:
                result = await session.run(query, limit=limit)
                records = await result.data()
                return records

        except Exception as e:
            logger.error(f"Error getting all skills: {e}")
            return []

    # Cache for get_all_skills to reduce Neo4j queries
    _skills_cache: Dict[str, Any] = {"data": None, "timestamp": 0}
    _skills_cache_lock: asyncio.Lock = None
    _SKILLS_CACHE_TTL: int = 300  # 5 minutes

    async def get_all_skills_cached(self, limit: int = 300) -> List[Dict[str, Any]]:
        """
        Get all skills with caching (5 minute TTL).

        Used for LLM prompt context to avoid repeated Neo4j queries
        during high-volume resume/JD processing.
        """
        # Initialize lock if needed (can't do in class body for async)
        if self._skills_cache_lock is None:
            self._skills_cache_lock = asyncio.Lock()

        async with self._skills_cache_lock:
            now = time.time()

            # Return cached data if still valid
            if (self._skills_cache["data"] is not None and
                (now - self._skills_cache["timestamp"]) < self._SKILLS_CACHE_TTL):
                return self._skills_cache["data"]

            # Fetch fresh data
            skills = await self.get_all_skills(limit)
            self._skills_cache["data"] = skills
            self._skills_cache["timestamp"] = now
            logger.debug(f"Refreshed skills cache with {len(skills)} skills")
            return skills

    def invalidate_skills_cache(self) -> None:
        """Invalidate the skills cache (call after adding new skills)."""
        self._skills_cache["data"] = None
        self._skills_cache["timestamp"] = 0

    # ========================================================================
    # Relationship Operations
    # ========================================================================

    async def create_has_skill_relationship(
        self,
        resume_id: str,
        skill_name: str,
        proficiency: str,
        years: Optional[int] = None
    ) -> bool:
        """Create HAS_SKILL relationship between resume and skill."""
        driver = await self._get_async_driver()

        query = """
        MATCH (r:Resume {id: $resume_id})
        MERGE (s:Skill {name: $skill_name})
        MERGE (r)-[rel:HAS_SKILL]->(s)
        SET rel.proficiency = $proficiency,
            rel.years = $years
        RETURN rel
        """

        try:
            async with driver.session() as session:
                await session.run(
                    query,
                    resume_id=resume_id,
                    skill_name=skill_name,
                    proficiency=proficiency,
                    years=years
                )
                return True

        except Exception as e:
            logger.error(f"Error creating HAS_SKILL relationship: {e}")
            raise

    async def create_requires_relationship(
        self,
        job_id: str,
        requirement_text: str
    ) -> bool:
        """Create REQUIRES relationship between job and requirement."""
        driver = await self._get_async_driver()

        query = """
        MATCH (j:JobDescription {id: $job_id})
        MERGE (req:Requirement {text: $text, job_id: $job_id})
        MERGE (j)-[:REQUIRES]->(req)
        RETURN req
        """

        try:
            async with driver.session() as session:
                await session.run(
                    query,
                    job_id=job_id,
                    text=requirement_text
                )
                return True

        except Exception as e:
            logger.error(f"Error creating REQUIRES relationship: {e}")
            raise

    async def create_match_relationship(
        self,
        resume_id: str,
        job_id: str,
        score: float,
        gaps: List[str]
    ) -> bool:
        """Create MATCHED_TO relationship between resume and job."""
        driver = await self._get_async_driver()

        query = """
        MATCH (r:Resume {id: $resume_id})
        MATCH (j:JobDescription {id: $job_id})
        MERGE (r)-[m:MATCHED_TO]->(j)
        SET m.score = $score,
            m.gaps = $gaps,
            m.created_at = datetime()
        RETURN m
        """

        try:
            async with driver.session() as session:
                await session.run(
                    query,
                    resume_id=resume_id,
                    job_id=job_id,
                    score=score,
                    gaps=gaps
                )
                return True

        except Exception as e:
            logger.error(f"Error creating MATCHED_TO relationship: {e}")
            raise

    # ========================================================================
    # Vector Operations
    # ========================================================================

    async def store_embedding(
        self,
        node_type: str,
        node_id: str,
        embedding: List[float]
    ) -> bool:
        """Store embedding vector on a node."""
        driver = await self._get_async_driver()

        query = f"""
        MATCH (n:{node_type} {{id: $id}})
        SET n.embedding = $embedding
        RETURN n
        """

        try:
            async with driver.session() as session:
                await session.run(query, id=node_id, embedding=embedding)
                return True

        except Exception as e:
            logger.error(f"Error storing embedding: {e}")
            raise

    async def vector_similarity_search(
        self,
        node_type: str,
        embedding: List[float],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find similar nodes by vector similarity.

        Uses Neo4j's vector index if available, falls back to brute force.
        """
        driver = await self._get_async_driver()

        # Try using vector index (Neo4j 5.11+)
        query = f"""
        MATCH (n:{node_type})
        WHERE n.embedding IS NOT NULL
        WITH n, gds.similarity.cosine(n.embedding, $embedding) AS score
        ORDER BY score DESC
        LIMIT $top_k
        RETURN n.id as id, n as node, score
        """

        try:
            async with driver.session() as session:
                result = await session.run(
                    query,
                    embedding=embedding,
                    top_k=top_k
                )
                records = await result.data()

                return [
                    {
                        "id": r["id"],
                        "node": dict(r["node"]),
                        "score": r["score"]
                    }
                    for r in records
                ]

        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            return []

    # ========================================================================
    # Query Operations
    # ========================================================================

    async def get_resume_skills(self, resume_id: str) -> List[Dict[str, Any]]:
        """Get all skills for a resume."""
        driver = await self._get_async_driver()

        query = """
        MATCH (r:Resume {id: $id})-[rel:HAS_SKILL]->(s:Skill)
        RETURN s.name as name, s.category as category,
               rel.level as level, rel.years as years
        """

        try:
            async with driver.session() as session:
                result = await session.run(query, id=resume_id)
                return await result.data()

        except Exception as e:
            logger.error(f"Error getting resume skills: {e}")
            return []

    async def find_matching_jobs(self, resume_id: str) -> List[Dict[str, Any]]:
        """Find jobs that match a resume's skills."""
        driver = await self._get_async_driver()

        query = """
        MATCH (r:Resume {id: $id})-[:HAS_SKILL]->(s:Skill)<-[:REQUIRES_SKILL]-(j:JobDescription)
        WITH j, count(s) as matching_skills
        RETURN j.id as job_id, j.title as title, j.company as company,
               matching_skills
        ORDER BY matching_skills DESC
        """

        try:
            async with driver.session() as session:
                result = await session.run(query, id=resume_id)
                return await result.data()

        except Exception as e:
            logger.error(f"Error finding matching jobs: {e}")
            return []

    async def get_skill_gaps(
        self,
        resume_id: str,
        job_id: str
    ) -> List[Dict[str, Any]]:
        """Get skills required by job but missing from resume."""
        driver = await self._get_async_driver()

        query = """
        MATCH (j:JobDescription {id: $job_id})-[req:REQUIRES_SKILL]->(s:Skill)
        WHERE NOT EXISTS {
            MATCH (r:Resume {id: $resume_id})-[:HAS_SKILL]->(s)
        }
        RETURN s.name as skill_name, s.category as category,
               req.type as importance, req.level as required_level
        """

        try:
            async with driver.session() as session:
                result = await session.run(
                    query,
                    resume_id=resume_id,
                    job_id=job_id
                )
                return await result.data()

        except Exception as e:
            logger.error(f"Error getting skill gaps: {e}")
            return []

    # ========================================================================
    # Session Operations
    # ========================================================================

    async def save_session(self, session_data: Dict[str, Any]) -> bool:
        """Save session data to graph."""
        driver = await self._get_async_driver()

        query = """
        MERGE (s:Session {session_id: $session_id})
        SET s.resume_id = $resume_id,
            s.job_ids = $job_ids,
            s.created_at = $created_at,
            s.updated_at = datetime()
        RETURN s
        """

        try:
            async with driver.session() as session:
                await session.run(query, **session_data)
                return True

        except Exception as e:
            logger.error(f"Error saving session: {e}")
            raise

    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data."""
        driver = await self._get_async_driver()

        query = """
        MATCH (s:Session {session_id: $session_id})
        RETURN s
        """

        try:
            async with driver.session() as session:
                result = await session.run(query, session_id=session_id)
                record = await result.single()
                return dict(record["s"]) if record else None

        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """Delete session and related temporary data."""
        driver = await self._get_async_driver()

        query = """
        MATCH (s:Session {session_id: $session_id})
        DETACH DELETE s
        """

        try:
            async with driver.session() as session:
                await session.run(query, session_id=session_id)
                return True

        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            raise

    # ========================================================================
    # Direct Vector Search Operations (Neo4j native, not LlamaIndex)
    # ========================================================================

    async def store_skill_embedding(
        self,
        skill_name: str,
        embedding: List[float],
        category: Optional[str] = None
    ) -> bool:
        """
        Store embedding on a Skill node for direct vector search.

        Args:
            skill_name: Name of the skill
            embedding: 768-dimensional embedding vector
            category: Optional skill category

        Returns:
            True if successful
        """
        driver = await self._get_async_driver()

        query = """
        MERGE (s:Skill {name: $name})
        SET s.embedding = $embedding,
            s.category = COALESCE($category, s.category),
            s.embedding_updated_at = datetime()
        RETURN s.name
        """

        try:
            async with driver.session() as session:
                await session.run(
                    query,
                    name=skill_name,
                    embedding=embedding,
                    category=category
                )
                return True
        except Exception as e:
            logger.error(f"Error storing skill embedding: {e}")
            return False

    async def find_similar_resume_skills(
        self,
        job_skill_embedding: List[float],
        resume_id: str,
        threshold: float = 0.75,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find resume skills similar to a job skill using direct Neo4j vector search.

        Combines vector similarity WITH graph traversal in a single query.
        This is more efficient than LlamaIndex because it:
        1. Only searches skills linked to this resume (graph-aware)
        2. Returns skill metadata in the same query
        3. No middleware overhead

        Args:
            job_skill_embedding: Embedding vector for the job skill
            resume_id: Resume ID to search within
            threshold: Minimum similarity score (0-1)
            limit: Maximum results to return

        Returns:
            List of matching skills with scores and metadata
        """
        driver = await self._get_async_driver()

        # Graph-aware vector search: only search skills linked to this resume
        # Using manual cosine similarity calculation (works without GDS plugin)
        query = """
        MATCH (r:Resume {id: $resume_id})-[rel:HAS_SKILL]->(s:Skill)
        WHERE s.embedding IS NOT NULL
        WITH s, rel,
             reduce(dot = 0.0, i IN range(0, size(s.embedding)-1) |
                    dot + s.embedding[i] * $embedding[i]) /
             (sqrt(reduce(a = 0.0, i IN range(0, size(s.embedding)-1) |
                    a + s.embedding[i] * s.embedding[i])) *
              sqrt(reduce(b = 0.0, i IN range(0, size($embedding)-1) |
                    b + $embedding[i] * $embedding[i]))) AS similarity
        WHERE similarity > $threshold
        RETURN s.name AS skill_name,
               s.category AS category,
               rel.level AS level,
               rel.years_experience AS years_experience,
               similarity AS score
        ORDER BY similarity DESC
        LIMIT $limit
        """

        try:
            # Use READ access mode - this is a read-only query
            # Prevents "Failed to obtain connection towards 'WRITE' server" error
            from neo4j import READ_ACCESS
            async with driver.session(default_access_mode=READ_ACCESS) as session:
                result = await session.run(
                    query,
                    embedding=job_skill_embedding,
                    resume_id=resume_id,
                    threshold=threshold,
                    limit=limit
                )
                return await result.data()
        except Exception as e:
            logger.error(f"Error in vector skill search: {e}")
            return []

    async def find_similar_skills_by_embedding(
        self,
        embedding: List[float],
        threshold: float = 0.92,
        limit: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Find skills similar to an embedding across ALL skill nodes.

        Used for skill normalization/deduplication: given a new skill's
        embedding, find if a similar skill already exists in the graph.

        Args:
            embedding: Embedding vector to search for
            threshold: Minimum similarity score (0-1), default 0.92 for strict matching
            limit: Maximum results to return

        Returns:
            List of matching skills with name, category, and similarity score
        """
        driver = await self._get_async_driver()

        query = """
        MATCH (s:Skill)
        WHERE s.embedding IS NOT NULL
        WITH s,
             reduce(dot = 0.0, i IN range(0, size(s.embedding)-1) |
                    dot + s.embedding[i] * $embedding[i]) /
             (sqrt(reduce(a = 0.0, i IN range(0, size(s.embedding)-1) |
                    a + s.embedding[i] * s.embedding[i])) *
              sqrt(reduce(b = 0.0, i IN range(0, size($embedding)-1) |
                    b + $embedding[i] * $embedding[i]))) AS similarity
        WHERE similarity > $threshold
        RETURN s.name AS name,
               s.category AS category,
               similarity AS score
        ORDER BY similarity DESC
        LIMIT $limit
        """

        try:
            from neo4j import READ_ACCESS
            async with driver.session(default_access_mode=READ_ACCESS) as session:
                result = await session.run(
                    query,
                    embedding=embedding,
                    threshold=threshold,
                    limit=limit
                )
                return await result.data()
        except Exception as e:
            logger.error(f"Error in global skill vector search: {e}")
            return []

    async def batch_find_similar_skills(
        self,
        job_skill_embeddings: Dict[str, List[float]],
        resume_id: str,
        threshold: float = 0.75
    ) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Batch find similar skills for multiple job skills in parallel.

        Args:
            job_skill_embeddings: Dict of {skill_name: embedding}
            resume_id: Resume ID to search within
            threshold: Minimum similarity score

        Returns:
            Dict of {job_skill_name: matching_resume_skill_or_None}
        """
        import asyncio

        async def find_one(skill_name: str, embedding: List[float]):
            results = await self.find_similar_resume_skills(
                job_skill_embedding=embedding,
                resume_id=resume_id,
                threshold=threshold,
                limit=1
            )
            return skill_name, results[0] if results else None

        tasks = [
            find_one(name, emb)
            for name, emb in job_skill_embeddings.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {
            name: match
            for name, match in results
            if not isinstance(match, Exception)
        }


# Singleton instance
_neo4j_store: Optional[Neo4jStore] = None


def get_neo4j_store() -> Neo4jStore:
    """Get singleton Neo4j store instance."""
    global _neo4j_store
    if _neo4j_store is None:
        _neo4j_store = Neo4jStore()
    return _neo4j_store

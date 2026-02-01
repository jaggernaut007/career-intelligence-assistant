# Neo4j Database Schema

The Career Intelligence Assistant uses Neo4j for both graph storage and vector similarity search.

## Overview

Neo4j provides:
- **Graph relationships** between resumes, skills, and jobs
- **Vector indexes** for semantic skill matching
- **ACID transactions** for data consistency

## Connection Configuration

```python
MAX_CONNECTION_POOL_SIZE = 50      # Concurrent connections
CONNECTION_ACQUISITION_TIMEOUT = 60 # Wait time for connection
MAX_CONNECTION_LIFETIME = 3600     # Connection lifetime (1 hour)
CONNECTION_TIMEOUT = 30            # Establishment timeout
```

---

## Node Types

### Resume

Stores parsed resume information.

```cypher
(:Resume {
    id: string,              // UUID - primary key
    summary: string,         // Professional summary
    contact_redacted: boolean, // True if PII was found and redacted
    updated_at: datetime
})
```

### Skill

Normalized skill nodes shared across resumes and jobs.

```cypher
(:Skill {
    name: string,            // Normalized skill name (e.g., "React")
    category: string,        // programming, framework, tool, soft_skill, domain
    embedding: float[768],   // Nomic embedding vector
    embedding_updated_at: datetime
})
```

**Skill Categories**:
- `programming` - Languages (Python, JavaScript, etc.)
- `framework` - Frameworks (React, FastAPI, etc.)
- `tool` - Tools (Docker, Git, etc.)
- `soft_skill` - Communication, Leadership, etc.
- `domain` - Industry knowledge (Finance, Healthcare, etc.)

### JobDescription

Stores parsed job requirements.

```cypher
(:JobDescription {
    id: string,              // UUID - primary key
    title: string,           // Job title
    company: string,         // Company name
    experience_years_min: integer,
    experience_years_max: integer,
    updated_at: datetime
})
```

### Experience

Work experience entries linked to resumes.

```cypher
(:Experience {
    resume_id: string,       // Parent resume ID
    title: string,           // Job title
    company: string,         // Company name
    duration: string,        // "2 years", "Jan 2020 - Present"
    duration_months: integer, // Normalized months
    description: string      // Role description
})
```

### Education

Education entries linked to resumes.

```cypher
(:Education {
    resume_id: string,       // Parent resume ID
    degree: string,          // "Bachelor of Science"
    institution: string,     // "MIT"
    year: integer,           // Graduation year
    gpa: float,              // Optional GPA
    field_of_study: string   // "Computer Science"
})
```

### Session

Tracks user analysis sessions.

```cypher
(:Session {
    session_id: string,      // Session UUID
    resume_id: string,       // Uploaded resume ID
    job_ids: string[],       // Array of job IDs
    created_at: datetime,
    updated_at: datetime
})
```

---

## Relationships

### HAS_SKILL

Links resumes to their skills.

```cypher
(:Resume)-[:HAS_SKILL {
    level: string,           // beginner, intermediate, advanced, expert
    years_experience: integer // Optional years of experience
}]->(:Skill)
```

### REQUIRES_SKILL

Links job descriptions to required skills.

```cypher
(:JobDescription)-[:REQUIRES_SKILL {
    type: string,            // "required" or "nice_to_have"
    level: string            // Required proficiency level
}]->(:Skill)
```

### MATCHED_TO

Records skill match results between resume and job.

```cypher
(:Resume)-[:MATCHED_TO {
    score: float,            // Fit score (0-100)
    gaps: string[],          // List of missing skills
    created_at: datetime
}]->(:JobDescription)
```

### HAS_EXPERIENCE

Links resumes to work experience entries.

```cypher
(:Resume)-[:HAS_EXPERIENCE]->(:Experience)
```

### HAS_EDUCATION

Links resumes to education entries.

```cypher
(:Resume)-[:HAS_EDUCATION]->(:Education)
```

---

## Graph Schema Diagram

```
                    ┌──────────┐
                    │  Resume  │
                    │    id    │
                    │ summary  │
                    └────┬─────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    HAS_SKILL     HAS_EXPERIENCE   HAS_EDUCATION
         │               │               │
         ▼               ▼               ▼
    ┌─────────┐    ┌──────────┐    ┌───────────┐
    │  Skill  │    │Experience│    │ Education │
    │  name   │    │  title   │    │  degree   │
    │category │    │ company  │    │institution│
    │embedding│    │ duration │    │   year    │
    └────┬────┘    └──────────┘    └───────────┘
         │
         │ REQUIRES_SKILL
         │
         ▼
    ┌────────────────┐
    │ JobDescription │
    │     title      │
    │    company     │
    └────────────────┘
```

---

## Vector Indexes

### Skill Embedding Index

Used for semantic skill matching (e.g., "React" ~ "ReactJS").

```cypher
CREATE VECTOR INDEX skill_embedding_index IF NOT EXISTS
FOR (s:Skill)
ON s.embedding
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 768,
        `vector.similarity_function`: 'cosine'
    }
}
```

### Vector Search Query

Finding similar skills using cosine similarity:

```cypher
MATCH (r:Resume {id: $resume_id})-[rel:HAS_SKILL]->(s:Skill)
WHERE s.embedding IS NOT NULL
WITH s, rel,
     reduce(dot = 0.0, i IN range(0, size(s.embedding)-1) |
            dot + s.embedding[i] * $query_embedding[i]) /
     (sqrt(reduce(a = 0.0, i IN range(0, size(s.embedding)-1) |
            a + s.embedding[i] * s.embedding[i])) *
      sqrt(reduce(b = 0.0, i IN range(0, size($query_embedding)-1) |
            b + $query_embedding[i] * $query_embedding[i]))) AS similarity
WHERE similarity > 0.75
RETURN s.name, similarity
ORDER BY similarity DESC
```

---

## Common Queries

### Get Resume with All Skills

```cypher
MATCH (r:Resume {id: $id})
OPTIONAL MATCH (r)-[hs:HAS_SKILL]->(s:Skill)
RETURN r,
       collect({
           name: s.name,
           category: s.category,
           level: hs.level,
           years_experience: hs.years_experience
       }) as skills
```

### Find Skill Gaps

```cypher
MATCH (j:JobDescription {id: $job_id})-[req:REQUIRES_SKILL]->(s:Skill)
WHERE NOT EXISTS {
    MATCH (r:Resume {id: $resume_id})-[:HAS_SKILL]->(s)
}
RETURN s.name as skill_name,
       s.category as category,
       req.type as importance
```

### Get All Skills for LLM Context

```cypher
MATCH (s:Skill)
WHERE s.name IS NOT NULL
RETURN s.name AS name, s.category AS category
ORDER BY s.name
LIMIT 500
```

---

## Caching Strategy

### Skills Cache

The application caches skill nodes for LLM prompts (5-minute TTL):

```python
_SKILLS_CACHE_TTL = 300  # 5 minutes

async def get_all_skills_cached(self, limit: int = 300):
    """Returns cached skills for LLM prompt context."""
```

### Cache Invalidation

Call after adding new skills:

```python
neo4j_store.invalidate_skills_cache()
```

---

## Constraints and Indexes

### Unique Constraints

```cypher
CREATE CONSTRAINT resume_id IF NOT EXISTS
FOR (r:Resume) REQUIRE r.id IS UNIQUE;

CREATE CONSTRAINT job_id IF NOT EXISTS
FOR (j:JobDescription) REQUIRE j.id IS UNIQUE;

CREATE CONSTRAINT skill_name IF NOT EXISTS
FOR (s:Skill) REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT session_id IF NOT EXISTS
FOR (s:Session) REQUIRE s.session_id IS UNIQUE;
```

### Performance Indexes

```cypher
CREATE INDEX skill_category IF NOT EXISTS
FOR (s:Skill) ON (s.category);

CREATE INDEX experience_resume IF NOT EXISTS
FOR (e:Experience) ON (e.resume_id);

CREATE INDEX education_resume IF NOT EXISTS
FOR (ed:Education) ON (ed.resume_id);
```

---

## Data Retention

Sessions and temporary data are cleaned up periodically. Skill nodes persist across sessions to improve the skill normalization graph over time.

# Career Intelligence Platform
## 1. Setup and Installation Guide
1. **Clone the Repository**
   ```bash
   git clone git@github.com:jaggernaut007/career-intelligence-assistant.git
   cd career-intelligence-assistant
   ```

2. **Setup Neo4j AuraDB** — Create a free instance at [Neo4j AuraDB](https://neo4j.com/cloud/aura/)

3. **Obtain API Keys** — Get keys from [OpenAI](https://platform.openai.com/api-keys) and [Hugging Face](https://huggingface.co/settings/tokens)

4. **Set Up Environment Variables**
   ```bash
   cp .env.example .env
   # Edit .env with your keys:
   # NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD
   # OPENAI_API_KEY, HF_TOKEN
   ```

   **Environment file locations:**
   | Scenario | .env Location | Notes |
   |----------|---------------|-------|
   | Local development | `backend/.env` | Required when running `uv run uvicorn` from backend/ |
   | Docker Compose | `root/.env` | Required for `docker-compose up` |

   > **Tip:** To keep both in sync, you can create a symlink: `cd backend && ln -s ../.env .env`

5. **Install Dependencies**
   ```bash
   uv sync
   ```

6. **Run the Application**
   ```bash
   # Frontend
   cd frontend && npm install && npm run dev

   # Backend (new terminal)
   uv run uvicorn main:app --reload
   ```

7. **Run Tests**
   ```bash
   uv run pytest
   ```

8. **Using Docker (Alternative to steps 5-7)**

   **Prerequisites:** Ensure Docker and Docker Compose are installed on your system.

   **Development Mode:**
   ```bash
   # Build and run with hot reload
   docker-compose up --build


   # Stop containers
   docker-compose down
   ```

   **Access Points:**
   | Service | Development |
   |---------|-------------|
   | Frontend | http://localhost:5173 | 
   | Backend API | http://localhost:8000 | 
   | API Docs | http://localhost:8000/docs |

## 2. Usage Instructions
1. Open your web browser and navigate to `http://localhost:5123` to access the Career Intelligence Platform.
2. Upload your resume and job descriptions.
3. Navigate to analysis and insights sections to explore the features of the platform.
4. Use the chat interface to interact with the AI assistant for career advice and insights.

## 3. Features Overview
- **Resume Analysis**: Upload and analyze resumes for skill gaps and improvements.
- **Job Description Comparison**: Compare resumes against up to 5 job descriptions to identify matches.
- **Skill Development Recommendations**: Get recommendations for skill development based on job market trends.
- **Interview Preparation**: Interview tips and common questions and sample answers.
- **Market Trends Analysis**: Stay updated with the latest trends in your industry.
- **AI-Powered Chat**: Interact with an AI assistant for personalized career advice.

## 4. Key Decisions Made
- **Neo4j AuraDB**: Chosen for its robust graph database capabilities, ideal for modeling complex relationships in career data vs Pinecone which was considered but not selected due to its efficiency in handling vector data but less suited for relational data modeling.
- **OpenAI**: Selected GPT-5.2 for its high reasoning capabilities enhancing the AI assistant's performance in understanding and generating human-like text.
- **FastAPI and React**: Used for backend and frontend development respectively, for multi-threading and fast development and servers.
- **UV package manager**: Utilized for efficient dependency management and environment setup.
- **LlamaIndex**: Employed for building a knowledge graph from unstructured data, enhancing the AI's understanding of career-related information. Its efficiency in RAG workloads. Its workflow framework was leveraged to implement a multi-agentic approach, allowing different AI models to specialize in various tasks vs LangGraph which was considered but not selected due to its complexity and overhead for this specific use case.
- **Nomic Embed Text v1.5**: Used nomic-embed-text-v1.5 embeddings for generating high-quality text embeddings to improve semantic search and recommendations, on-device with high latency vs other embedding models which were considered but not selected due to their lower performance in this context.
- **Docker**: Considered for containerization, if we would need to deploy, but opted for local setup to simplify initial development and testing.
- **Modular Architecture**: Designed the application with a modular approach to facilitate future enhancements and maintenance. Easy to use service-oriented and model layers based architecture.
- **OpenAI GPT-5.2**: Leveraged for its superior language understanding and generation capabilities, enhancing the AI assistant's performance in providing career advice and insights.
- **Claude Code Interpreter**: Integrated for its advanced code interpretation features, and ability to handle complex coding tasks while pair programming.
- **Test-Driven and Spec-Supported Development**: Adopted TDD approach to ensure code quality and reliability through comprehensive testing and spec-driven development practices for clear requirements and functionality definition to ensure the AI understands everything deterministically.

## 5. Detailed decisions made
- **Vectorisation Strategy**: Chose Nomic Embed Text v1.5 for its ability to generate high-quality text embeddings, which significantly improves the accuracy of semantic search and recommendations within the platform. This combined with the use of Neo4j Vector Search capabilities allows for efficient storage and retrieval of vector data through graph traversal and embedding comparison, enhancing the overall performance of the AI assistant.
- **Multi-agentic Approach**: Implemented a multi-agentic architecture using LlamaIndex workflow framework to allow different AI models to specialize in various tasks, such as resume analysis, job description comparison, interview preparation, recommendation and market analysis. This specialisation leads to more accurate and relevant responses for users.
- **Guardrails and Safety**: Implemented a 5-layer security architecture to ensure reliable and safe AI interactions. 
    - Layer 1: PII Detection using Microsoft Presidio with spaCy NLP to automatically detect and redact SSNs, phone numbers, emails, and addresses from resumes before processing.
    - Layer 2: Prompt Injection Guard using pattern matching to detect intrusion and security threats in user inputs before passing to LLMs.
    - Layer 3: Input Validation that verifies file types, enforces 10MB size limits, and blocks dangerous file types like executables and scripts. 
    - Layer 4: Rate Limiting via slowapi enforcing 10 requests/minute per session to prevent API abuse. 
    - Layer 5: Output Filtering that sanitizes LLM responses, strips leaked system prompts, and validates JSON structure before returning to the frontend.
- **Phase-by-Phase Rollout**: Adopted a phased approach to development and testing framework with a spec-supported development to ensure that each feature is thoroughly vetted before being integrated into the main platform. This approach allows for incremental improvements and reduces the risk of introducing bugs or issues.
- **Wizard based Onboarding with chatbot**: Developed a user-friendly onboarding wizard to guide new users through the platform's features and functionalities, ensuring a smooth and intuitive user experience from the outset, while the chatbot provides real-time assistance and support.
- **Neo4j Deployment**: Opted for Neo4j AuraDB for its managed cloud service, which simplifies database management and scaling. This choice makes it easy to manage the graph database without the overhead of self-hosting, plus used caching strategies to optimize query performance and reduce latency.
- **In-Memory Session Management**: Chose in-memory session management for simplicity and speed during development. This approach allows for quick access to session data without the complexity of external session stores, making it ideal for the initial phases of the project.
- **Observability and Monitoring**: Integrated logging and monitoring tools to track application performance, user interactions, and potential issues. This setup helps in proactive maintenance and ensures a smooth user experience.
- **Evaluation and Benchmarking**: Established a framework for evaluating the performance of different AI models by using the concept of LLM as a judge to benchmark responses based on relevance, accuracy, and user satisfaction. This approach allows for continuous improvement of the AI assistant by identifying the best-performing models for specific tasks.
- **Resume and Job Processing Pipeline**: Developed a robust pipeline for processing resumes and job descriptions, including text extraction, cleaning, vectorization, and storage in Neo4j. This pipeline ensures that the data is accurately represented and easily retrievable for analysis and recommendations. We perform this by:
    - Text Extraction: Extract text from various document formats (PDF, DOCX).
    - Text Cleaning: Implementing NLP techniques to clean and preprocess the extracted text, removing noise and irrelevant information.
    - Using LLamaIndex to extract entities, skills, experiences, and other relevant information from the text.
    - Vectorization: Generating embeddings using Nomic Embed Text v1.5 for semantic representation of the text.
    - Storage: Storing the processed data in Neo4j with appropriate relationships to facilitate efficient querying and analysis.



## 6. Architecture Diagrams

### 6.1 System Overview

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    CAREER INTELLIGENCE PLATFORM                               │
├──────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  ┌─────────────────────────────────────────┐      ┌─────────────────────────────────────┐   │
│  │           FRONTEND (React 18)           │      │         EXTERNAL SERVICES           │   │
│  │  ┌─────────────────────────────────┐   │      │  ┌─────────────────────────────┐    │   │
│  │  │  Wizard Flow (4 Steps)          │   │      │  │      OpenAI API (GPT)       │    │   │
│  │  │  • Upload Resume                │   │      │  │  • Structured extraction    │    │   │
│  │  │  • Add Job Descriptions (≤5)    │   │      │  │  • Agent reasoning          │    │   │
│  │  │  • Run Analysis                 │   │      │  │  • Chat responses           │    │   │
│  │  │  • Explore Results              │   │      │  └─────────────────────────────┘    │   │
│  │  └─────────────────────────────────┘   │      │  ┌─────────────────────────────┐    │   │
│  │  ┌─────────────────────────────────┐   │      │  │   HuggingFace Inference     │    │   │
│  │  │  State Management               │   │      │  │  • nomic-embed-text-v1.5    │    │   │
│  │  │  • Zustand (UI state)           │   │      │  │  • 768-dim embeddings       │    │   │
│  │  │  • React Query (server state)   │   │      │  └─────────────────────────────┘    │   │
│  │  └─────────────────────────────────┘   │      │  ┌─────────────────────────────┐    │   │
│  │  ┌─────────────────────────────────┐   │      │  │     Neo4j AuraDB            │    │   │
│  │  │  Chat Interface                 │   │      │  │  • Graph relationships      │    │   │
│  │  │  • Real-time Q&A                │   │      │  │  • Vector similarity        │    │   │
│  │  │  • Suggested questions          │   │      │  │  • Skill normalization      │    │   │
│  │  └─────────────────────────────────┘   │      │  └─────────────────────────────┘    │   │
│  └───────────────────┬─────────────────────┘      └──────────────────┬──────────────────┘   │
│                      │                                               │                      │
│                      │ HTTP/REST + WebSocket                         │                      │
│                      ▼                                               │                      │
│  ┌───────────────────────────────────────────────────────────────────┴──────────────────┐   │
│  │                              BACKEND (FastAPI + Python 3.11)                          │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │                            5-LAYER SECURITY GUARDRAILS                           │ │   │
│  │  │  ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────┐ ┌───────────────────┐  │ │   │
│  │  │  │   PII     │ │  Prompt   │ │   Input   │ │   Rate    │ │     Output        │  │ │   │
│  │  │  │ Detection │→│ Injection │→│Validation │→│ Limiting  │→│    Filtering      │  │ │   │
│  │  │  │(Presidio) │ │   Guard   │ │(File/Size)│ │(10/min)   │ │  (Sanitization)   │  │ │   │
│  │  │  └───────────┘ └───────────┘ └───────────┘ └───────────┘ └───────────────────┘  │ │   │
│  │  └─────────────────────────────────────────────────────────────────────────────────┘ │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │                              API LAYER                                           │ │   │
│  │  │  /session  /upload/resume  /upload/job-description  /analyze  /results  /chat   │ │   │
│  │  └──────────────────────────────────────┬──────────────────────────────────────────┘ │   │
│  │                                         │                                            │   │
│  │                                         ▼                                            │   │
│  │  ┌─────────────────────────────────────────────────────────────────────────────────┐ │   │
│  │  │                    LLAMAINDEX WORKFLOW ENGINE                                    │ │   │
│  │  │                      (Event-Driven Multi-Agent)                                  │ │   │
│  │  │                         (See Diagram 6.2)                                        │ │   │
│  │  └─────────────────────────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 LlamaIndex Workflow (Event-Driven Multi-Agent)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                        LLAMAINDEX WORKFLOW: EVENT-DRIVEN EXECUTION                           │
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                         CareerAnalysisWorkflow(Workflow)                             │   │
│   │                                                                                      │   │
│   │   ctx.store (Shared State)           @step decorators (Parallel Execution)           │   │
│   │   • session_id                       • num_workers for concurrency                   │   │
│   │   • parsed_jobs: Dict                • Typed events for communication                │   │
│   │   • skill_matches: Dict              • ctx.send_event() for dispatch                 │   │
│   │   • completed_steps: List                                                            │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                             │                                               │
│                                             │ StartAnalysisEvent                            │
│                                             ▼                                               │
│   ══════════════════════════════════════════════════════════════════════════════════════   │
│   ║                           PHASE 1: DOCUMENT PARSING                                ║   │
│   ║                           ctx.send_event() dispatches multiple events              ║   │
│   ══════════════════════════════════════════════════════════════════════════════════════   │
│                                             │                                               │
│              ┌──────────────────────────────┼──────────────────────────────┐               │
│              │                              │                              │               │
│              ▼                              ▼                              ▼               │
│   ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐         │
│   │  ResumeParseEvent   │     │   JDAnalyzeEvent    │     │   JDAnalyzeEvent    │         │
│   └──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘         │
│              │                           │                           │                     │
│              ▼                           ▼                           ▼                     │
│   ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐         │
│   │    @step            │     │    @step            │     │    @step            │         │
│   │  parse_resume       │     │   analyze_jd        │     │   analyze_jd        │         │
│   │  ───────────────    │     │   ───────────       │     │   (Job N...)        │         │
│   │ • PII Redaction     │     │ • Title extraction  │     │                     │         │
│   │ • Skill extraction  │     │ • Required skills   │     │  (Up to 5 jobs      │         │
│   │ • Experience parse  │     │ • Nice-to-have      │     │   in parallel)      │         │
│   │ • Graph normalize   │     │ • Experience reqs   │     │                     │         │
│   │                     │     │                     │     │                     │         │
│   │ Duration: 15-25s    │     │ Duration: 10-15s    │     │                     │         │
│   └──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘         │
│              │                           │                           │                     │
│              ▼                           ▼                           ▼                     │
│   ┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐         │
│   │ResumeParseResultEvt │     │ JDAnalyzeResultEvt  │     │ JDAnalyzeResultEvt  │         │
│   └──────────┬──────────┘     └──────────┬──────────┘     └──────────┬──────────┘         │
│              │                           │                           │                     │
│              └───────────────────────────┼───────────────────────────┘                     │
│                                          │                                                  │
│                            @step collect_phase1_results                                     │
│                            (waits for all Phase 1 events)                                   │
│                                          │                                                  │
│   ══════════════════════════════════════╪═══════════════════════════════════════════       │
│   ║                         PHASE 2: SKILL MATCHING                                 ║       │
│   ║                         Parallel per job via ctx.send_event()                   ║       │
│   ══════════════════════════════════════╪═══════════════════════════════════════════       │
│                                         │                                                   │
│              ┌──────────────────────────┼──────────────────────────┐                       │
│              │                          │                          │                       │
│              ▼                          ▼                          ▼                       │
│   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐           │
│   │   SkillMatchEvent   │    │   SkillMatchEvent   │    │   SkillMatchEvent   │           │
│   │   (Job 1)           │    │   (Job 2)           │    │   (Job N)           │           │
│   └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘           │
│              │                          │                          │                       │
│              ▼                          ▼                          ▼                       │
│   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐           │
│   │    @step            │    │    @step            │    │    @step            │           │
│   │  match_skills       │    │  match_skills       │    │  match_skills       │           │
│   │  ─────────────      │    │  (parallel)         │    │                     │           │
│   │ • Exact matching    │    │                     │    │                     │           │
│   │ • Semantic match    │    │                     │    │                     │           │
│   │   (sim > 0.75)      │    │                     │    │                     │           │
│   │ • Graph traversal   │    │                     │    │                     │           │
│   │ • Fit score 0-100%  │    │                     │    │                     │           │
│   │                     │    │                     │    │                     │           │
│   │ Duration: 10-20s    │    │                     │    │                     │           │
│   └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘           │
│              │                          │                          │                       │
│              ▼                          ▼                          ▼                       │
│   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐           │
│   │SkillMatchResultEvt  │    │SkillMatchResultEvt  │    │SkillMatchResultEvt  │           │
│   └──────────┬──────────┘    └──────────┬──────────┘    └──────────┬──────────┘           │
│              │                          │                          │                       │
│              └──────────────────────────┼──────────────────────────┘                       │
│                                         │                                                   │
│                           @step collect_phase2_results                                      │
│                                         │                                                   │
│   ════════════════════════════════════╪═════════════════════════════════════════════       │
│   ║                       PHASE 3: ADVANCED ANALYSIS                                ║       │
│   ║                       Three parallel events dispatched                          ║       │
│   ════════════════════════════════════╪═════════════════════════════════════════════       │
│                                       │                                                     │
│              ┌────────────────────────┼────────────────────────┐                           │
│              │                        │                        │                           │
│              ▼                        ▼                        ▼                           │
│   ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐                 │
│   │GenerateRecommend- │    │GenerateInterview- │    │GenerateMarket-    │                 │
│   │  ationsEvent      │    │    PrepEvent      │    │  InsightsEvent    │                 │
│   └─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘                 │
│             │                        │                        │                           │
│             ▼                        ▼                        ▼                           │
│   ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐                 │
│   │    @step          │    │    @step          │    │    @step          │                 │
│   │ generate_         │    │ generate_         │    │ generate_         │                 │
│   │ recommendations   │    │ interview_prep    │    │ market_insights   │                 │
│   │ ───────────────   │    │ ───────────────   │    │ ───────────────   │                 │
│   │ • Priority skills │    │ • Tech questions  │    │ • Salary ranges   │                 │
│   │ • Learning paths  │    │ • Behavioral Qs   │    │ • Demand trends   │                 │
│   │ • Resume tips     │    │ • STAR examples   │    │ • Top companies   │                 │
│   │ • Action items    │    │ • Qs to ask       │    │ • Related roles   │                 │
│   │                   │    │                   │    │                   │                 │
│   │ Duration: 10-15s  │    │ Duration: 10-15s  │    │ Duration: 5-10s   │                 │
│   └─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘                 │
│             │                        │                        │                           │
│             ▼                        ▼                        ▼                           │
│   ┌───────────────────┐    ┌───────────────────┐    ┌───────────────────┐                 │
│   │Recommendation-    │    │InterviewPrep-     │    │MarketInsights-    │                 │
│   │  ResultEvent      │    │  ResultEvent      │    │  ResultEvent      │                 │
│   └─────────┬─────────┘    └─────────┬─────────┘    └─────────┬─────────┘                 │
│             │                        │                        │                           │
│             └────────────────────────┼────────────────────────┘                           │
│                                      │                                                     │
│                        @step finalize → StopEvent                                          │
│                              (aggregate all results)                                       │
│                                      │                                                     │
│                                      ▼                                                     │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              CHAT FIT AGENT (On-Demand)                             │   │
│   │    • Separate from workflow, invoked via /chat endpoint                             │   │
│   │    • Uses session context (resume + jobs + match results from ctx.store)            │   │
│   │    • UK/EU market focus • Suggested follow-up questions                             │   │
│   │    • Duration: 3-8s per message                                                     │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

Total Analysis Time: ~70-90s (1 job) | ~80-120s (5 jobs)
Parallel execution via @step + ctx.send_event() reduces time by ~60%
```

### 6.3 Neo4j Graph + Vector Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                           NEO4J AURADB: GRAPH + VECTOR STORE                                │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                                  GRAPH SCHEMA                                        │   │
│   │                                                                                      │   │
│   │                              ┌──────────────────┐                                    │   │
│   │                              │     Session      │                                    │   │
│   │                              │  • session_id    │                                    │   │
│   │                              │  • created_at    │                                    │   │
│   │                              └────────┬─────────┘                                    │   │
│   │                                       │                                              │   │
│   │                    ┌──────────────────┴──────────────────┐                          │   │
│   │                    │                                     │                          │   │
│   │                    ▼                                     ▼                          │   │
│   │         ┌──────────────────┐                  ┌──────────────────┐                  │   │
│   │         │     Resume       │                  │  JobDescription  │                  │   │
│   │         │  • id (UUID)     │                  │  • id (UUID)     │                  │   │
│   │         │  • summary       │                  │  • title         │                  │   │
│   │         │  • contact_      │                  │  • company       │                  │   │
│   │         │    redacted      │                  │  • exp_years_min │                  │   │
│   │         └────────┬─────────┘                  │  • exp_years_max │                  │   │
│   │                  │                            └────────┬─────────┘                  │   │
│   │    ┌─────────────┼─────────────┐                       │                            │   │
│   │    │             │             │                       │                            │   │
│   │    ▼             ▼             ▼                       │                            │   │
│   │ ┌──────┐    ┌──────────┐  ┌───────────┐               │                            │   │
│   │ │Skill │    │Experience│  │ Education │               │                            │   │
│   │ └──┬───┘    └──────────┘  └───────────┘               │                            │   │
│   │    │                                                   │                            │   │
│   │    │                   ┌───────────────────────────────┘                            │   │
│   │    │                   │                                                            │   │
│   │    │                   ▼                                                            │   │
│   │    │         ┌───────────────────┐                                                  │   │
│   │    └────────►│      Skill        │◄─────── REQUIRES_SKILL ─────────────────────    │   │
│   │              │  • name           │         (type: required|nice_to_have)            │   │
│   │ HAS_SKILL    │  • category       │                                                  │   │
│   │ (level,      │  • embedding[768] │◄─────── Vector Index                             │   │
│   │  years)      └───────────────────┘         (cosine similarity)                      │   │
│   │                                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              VECTOR SEARCH WORKFLOW                                  │   │
│   │                                                                                      │   │
│   │   ┌─────────────┐    ┌─────────────────┐    ┌─────────────────────────────────┐     │   │
│   │   │ Input Skill │───►│ Nomic Embedding │───►│ skill_embedding_index           │     │   │
│   │   │ "ReactJS"   │    │ (768 dims)      │    │ vector.similarity: cosine       │     │   │
│   │   └─────────────┘    └─────────────────┘    │ threshold: 0.75                 │     │   │
│   │                                              └───────────────┬─────────────────┘     │   │
│   │                                                              │                       │   │
│   │                                                              ▼                       │   │
│   │   ┌──────────────────────────────────────────────────────────────────────────────┐  │   │
│   │   │ MATCH (s:Skill) WHERE s.embedding IS NOT NULL                                │  │   │
│   │   │ WITH s, vector.similarity.cosine(s.embedding, $query) AS score               │  │   │
│   │   │ WHERE score > 0.75                                                           │  │   │
│   │   │ RETURN s.name, score ORDER BY score DESC                                     │  │   │
│   │   └──────────────────────────────────────────────────────────────────────────────┘  │   │
│   │                                                              │                       │   │
│   │                                                              ▼                       │   │
│   │   ┌─────────────────────────────────────────────────────────────────────────────┐   │   │
│   │   │ Results: ["React" (0.98), "React.js" (0.95), "ReactJS" (1.0)]               │   │   │
│   │   └─────────────────────────────────────────────────────────────────────────────┘   │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              OPTIMIZATION STRATEGIES                                 │   │
│   │                                                                                      │   │
│   │   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────┐            │   │
│   │   │   Skills Cache     │  │  Connection Pool   │  │   Batch Vectors    │            │   │
│   │   │   ─────────────    │  │  ───────────────   │  │   ─────────────    │            │   │
│   │   │ • 5-min TTL        │  │ • 50 connections   │  │ • Parallel search  │            │   │
│   │   │ • LLM context      │  │ • 60s acquisition  │  │ • Reduced queries  │            │   │
│   │   │ • 20ms → 1ms       │  │ • 1hr lifetime     │  │ • 20% faster       │            │   │
│   │   └────────────────────┘  └────────────────────┘  └────────────────────┘            │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.4 Testing Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                    TESTING PIPELINE                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              BACKEND TESTS (pytest)                                  │   │
│   │                                                                                      │   │
│   │   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐     │   │
│   │   │    UNIT TESTS       │    │  INTEGRATION TESTS  │    │   CONTRACT TESTS    │     │   │
│   │   │    ──────────       │    │  ─────────────────  │    │   ──────────────    │     │   │
│   │   │ tests/unit/         │    │ tests/integration/  │    │ tests/contract/     │     │   │
│   │   │                     │    │                     │    │                     │     │   │
│   │   │ • Agent logic       │    │ • API endpoints     │    │ • OpenAPI spec      │     │   │
│   │   │ • Service functions │    │ • Neo4j queries     │    │   validation        │     │   │
│   │   │ • Guardrails        │    │ • Full workflows    │    │ • Request/response  │     │   │
│   │   │ • Data models       │    │ • WebSocket         │    │   schema matching   │     │   │
│   │   │                     │    │                     │    │ • specs/openapi.yaml│     │   │
│   │   │ Mocked: LLM, Neo4j  │    │ Uses: Test DB       │    │                     │     │   │
│   │   └─────────────────────┘    └─────────────────────┘    └─────────────────────┘     │   │
│   │                                                                                      │   │
│   │   Commands:                                                                          │   │
│   │   $ uv run pytest tests/unit -v              # Unit tests only                       │   │
│   │   $ uv run pytest tests/integration -v       # Integration tests                     │   │
│   │   $ uv run pytest tests/contract -v          # Contract tests                        │   │
│   │   $ uv run pytest --cov=app                  # With coverage                         │   │
│   │                                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                             FRONTEND TESTS (Vitest)                                  │   │
│   │                                                                                      │   │
│   │   ┌─────────────────────┐    ┌─────────────────────┐    ┌─────────────────────┐     │   │
│   │   │  COMPONENT TESTS    │    │    STORE TESTS      │    │    HOOK TESTS       │     │   │
│   │   │  ───────────────    │    │    ───────────      │    │    ──────────       │     │   │
│   │   │                     │    │                     │    │                     │     │   │
│   │   │ • React Testing Lib │    │ • Zustand stores    │    │ • useAnalysis       │     │   │
│   │   │ • Wizard components │    │ • State transitions │    │ • useWebSocket      │     │   │
│   │   │ • Result displays   │    │ • Action handlers   │    │ • useSession        │     │   │
│   │   │ • UI components     │    │                     │    │                     │     │   │
│   │   │                     │    │                     │    │                     │     │   │
│   │   │ MSW for API mocking │    │                     │    │                     │     │   │
│   │   └─────────────────────┘    └─────────────────────┘    └─────────────────────┘     │   │
│   │                                                                                      │   │
│   │   Commands:                                                                          │   │
│   │   $ npm test                    # Run all tests                                      │   │
│   │   $ npm run test:ui             # Interactive test UI                                │   │
│   │   $ npm run test:coverage       # Coverage report                                    │   │
│   │                                                                                      │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
│   ┌─────────────────────────────────────────────────────────────────────────────────────┐   │
│   │                            EVALUATION FRAMEWORK                                      │   │
│   │                                                                                      │   │
│   │   ┌───────────────────────────────────────────────────────────────────────────┐     │   │
│   │   │                         LLM-AS-JUDGE EVALUATION                           │     │   │
│   │   │                                                                           │     │   │
│   │   │   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                │     │   │
│   │   │   │   Agent     │────►│   Response  │────►│  LLM Judge  │                │     │   │
│   │   │   │   Output    │     │   + Context │     │ (GPT-5.2)   │                │     │   │
│   │   │   └─────────────┘     └─────────────┘     └──────┬──────┘                │     │   │
│   │   │                                                  │                        │     │   │
│   │   │                                                  ▼                        │     │   │
│   │   │                          ┌─────────────────────────────────────────┐      │     │   │
│   │   │                          │  Evaluation Metrics:                    │      │     │   │
│   │   │                          │  • Relevance (0-10)                     │      │     │   │
│   │   │                          │  • Accuracy (0-10)                      │      │     │   │
│   │   │                          │  • Completeness (0-10)                  │      │     │   │
│   │   │                          │  • User Satisfaction (0-10)             │      │     │   │
│   │   │                          └─────────────────────────────────────────┘      │     │   │
│   │   └───────────────────────────────────────────────────────────────────────────┘     │   │
│   └─────────────────────────────────────────────────────────────────────────────────────┘   │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 6.5 Data Flow Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              END-TO-END DATA FLOW                                            │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                             │
│  USER                                                                                       │
│    │                                                                                        │
│    │ 1. Upload Resume (PDF/DOCX/TXT)                                                        │
│    ▼                                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                              DOCUMENT PROCESSING                                     │    │
│  │  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐    ┌───────────────┐  │    │
│  │  │ File Upload   │───►│ Text Extract  │───►│ PII Detection │───►│ Redaction     │  │    │
│  │  │ (10MB max)    │    │ (PyMuPDF,     │    │ (Presidio +   │    │ [REDACTED]    │  │    │
│  │  │               │    │  python-docx) │    │  spaCy NLP)   │    │               │  │    │
│  │  └───────────────┘    └───────────────┘    └───────────────┘    └───────┬───────┘  │    │
│  └──────────────────────────────────────────────────────────────────────────┼──────────┘    │
│                                                                             │               │
│                                                                             ▼               │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                              LLM STRUCTURED EXTRACTION                               │    │
│  │  ┌───────────────────────────────────────────────────────────────────────────────┐  │    │
│  │  │                                                                               │  │    │
│  │  │  Clean Text ──► LlamaIndex + OpenAI ──► Structured JSON                       │  │    │
│  │  │                                                                               │  │    │
│  │  │  {                                                                            │  │    │
│  │  │    "skills": [{"name": "Python", "level": "expert", "years": 5}],            │  │    │
│  │  │    "experiences": [{"title": "Senior Engineer", "company": "..."}],          │  │    │
│  │  │    "education": [{"degree": "BS Computer Science", "institution": "..."}]    │  │    │
│  │  │  }                                                                            │  │    │
│  │  │                                                                               │  │    │
│  │  └───────────────────────────────────────────────────────────────────────────────┘  │    │
│  └───────────────────────────────────────────────────────────────────────┬─────────────┘    │
│                                                                          │                  │
│                                                                          ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                            GRAPH-AWARE SKILL NORMALIZATION                          │    │
│  │                                                                                      │    │
│  │   1. Fetch existing skills ──► Neo4j Graph (cached 5min)                            │    │
│  │   2. LLM normalizes with context: "Map 'ReactJS' to existing 'React'"               │    │
│  │   3. New skills ──► Generate embedding ──► Store in graph                           │    │
│  │   4. Deduplication via embedding similarity (>0.95 = same skill)                    │    │
│  │                                                                                      │    │
│  └───────────────────────────────────────────────────────────────────────┬─────────────┘    │
│                                                                          │                  │
│                                                                          ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                              NEO4J GRAPH STORAGE                                     │    │
│  │                                                                                      │    │
│  │   (Resume)──[:HAS_SKILL {level, years}]──►(Skill {name, embedding[768]})            │    │
│  │      │                                           ▲                                   │    │
│  │      │                                           │                                   │    │
│  │      ├──[:HAS_EXPERIENCE]──►(Experience)         │                                   │    │
│  │      │                                           │                                   │    │
│  │      └──[:HAS_EDUCATION]──►(Education)     [:REQUIRES_SKILL]                        │    │
│  │                                                  │                                   │    │
│  │   (JobDescription)───────────────────────────────┘                                   │    │
│  │                                                                                      │    │
│  └───────────────────────────────────────────────────────────────────────┬─────────────┘    │
│                                                                          │                  │
│                                                                          ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                              SKILL MATCHING ENGINE                                   │    │
│  │                                                                                      │    │
│  │   ┌─────────────────┐                                                               │    │
│  │   │ Matching Layers │                                                               │    │
│  │   ├─────────────────┤                                                               │    │
│  │   │ 1. Exact Match  │──► "Python" == "Python" ✓                                     │    │
│  │   │ 2. Semantic     │──► embedding_sim("React", "ReactJS") = 0.98 > 0.75 ✓          │    │
│  │   │ 3. Graph Walk   │──► (Python)──[:RELATED_TO]──►(Django) ✓                       │    │
│  │   │ 4. Weighted Sum │──► required_skills × 0.7 + nice_to_have × 0.3                 │    │
│  │   └─────────────────┘                                                               │    │
│  │                               │                                                      │    │
│  │                               ▼                                                      │    │
│  │                    Fit Score: 85% + Skill Gaps + Recommendations                    │    │
│  │                                                                                      │    │
│  └───────────────────────────────────────────────────────────────────────┬─────────────┘    │
│                                                                          │                  │
���                                                                          ▼                  │
│  ┌─────────────────────────────────────────────────────────────────────────────────────┐    │
│  │                              RESULTS DELIVERY                                        │    │
│  │                                                                                      │    │
│  │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐  │    │
│  │   │    Fit Score    │  │  Skill Gaps     │  │ Recommendations │  │  Interview    │  │    │
│  │   │    ─────────    │  │  ──────────     │  │ ───────────────  │  │  Prep         │  │    │
│  │   │   85%           │  │ • Kubernetes    │  │ • Learn K8s     │  │ • Tech Qs     │  │    │
│  │   │   ┌────────┐    │  │ • AWS           │  │ • Get AWS cert  │  │ • STAR        │  │    │
│  │   │   │████████│    │  │ • Terraform     │  │ • Update resume │  │   examples    │  │    │
│  │   │   └────────┘    │  │                 │  │                 │  │               │  │    │
│  │   └─────────────────┘  └─────────────────┘  └─────────────────┘  └───────────────┘  │    │
│  │                                                                                      │    │
│  │   + WebSocket real-time progress updates during analysis                            │    │
│  │   + Chat interface for follow-up questions                                          │    │
│  └─────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                             │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

## 7. Deferred Decisions
- **Pinecone vs Neo4j AuraDB**: Needed a database for both vector search and relationship modeling. Evaluated Pinecone for vectors but chose Neo4j AuraDB to unify graph relationships and vector embeddings in one store, eliminating ambiguous vector retrievals and enabling graph-traversal + similarity search in single queries using embedding properties.
- **LangGraph vs LlamaIndex**: Required a framework for multi-agent orchestration. Evaluated LangGraph but chose LlamaIndex workflow for its native Neo4j integration, simpler workflow API, and 35% better retrieval accuracy in RAG benchmarks, reducing development time while improving response quality.
- **Message Bus vs LlamaIndex Workflow**: Needed inter-agent communication for parallel processing. Evaluated Redis pub/sub and RabbitMQ messaging services but chose LlamaIndex's built-in workflow engine. Parallel execution was achieved. Trade-off: single-process only, but sufficient for demo scale with upgrade path to Redis if needed.
- **Generalist vs Specialized Agents**: Needed to balance accuracy against complexity. Chose 7 specialized agents (Resume Parser, JD Analyzer, Skill Matcher, Recommendation, Interview Prep, Market Insights, Chat Fit) over fewer generalists, achieving more focused prompts and enabling parallel execution that reduced analysis time by 60%.
- **Direct Vectorization vs Document Processing**: Needed to extract career data from resumes. Evaluated direct embedding by chunking the document, but chose structured NER extraction via GPT-5.2 to capture skills, experiences, and relationships, enabling richer graph modeling and more accurate skill-gap analysis than pure semantic search.
- **Graph-Aware Skill Normalization vs Simple Embedding**: Needed to handle skill variations ("React.js" vs "ReactJS"). Chose LLM extraction with Neo4j context over pure embedding similarity,or using a pure LLM based graph storage technique. Making the system self-improving as the graph grows. Optimized with 5-minute caching (20ms → 1ms) and parallel fallback (1.5s → 200ms), adding only 200-400ms total latency.

## 8. Future Enhancements
- **Enhanced Security Measures**: Implement advanced encryption techniques to further protect user data.
- **Better evaluations**: Integrate more comprehensive evaluation metrics and benchmarking tools to continuously assess and improve the AI models' performance as opposed to just LLM as judge.
- **Better Tracing and Observability**: Implement LLM tracing and enhanced logging for better monitoring and debugging.
- **Dexterity in LlamaIndex Workflow** : Explore more complex multi-agent workflows and dynamic task allocation based on real-time performance metrics.
- **Prompt Optimization**: Continuously refine and optimize prompts for better accuracy and relevance in AI responses based on traces and evaluations.
- **Better Resume Parsing**: Integrate more advanced NLP techniques for improved extraction of skills and experiences from resumes.
- **Knowledge Graph Enhancements**: More complex and in-depth knowledge graph relationships to capture nuanced skill interdependencies.
- **Enhanced User Interface**: Improve the frontend design for a more intuitive and engaging user experience.
- **Better Testing Coverage**: Expand the test suite to cover more edge cases and scenarios for increased reliability.
- **Better Caching Strategies**: Implement more sophisticated caching mechanisms to reduce latency and improve response times.
- **Optimized Token Tracking and Usage Monitoring**: Implement improved token tracking and usage monitoring to reduce costs and improve efficiency.


## 9. Remaining Questions from requirements doc

1. What would be required to productionize your solution, make it scalable and deploy it on a hyper-scaler such as AWS / GCP / Azure?
   - The containerised application can be deployed using Docker on a cloud platform like AWS using services such as ECS or EKS for scalability. We could use auto-scaling groups, load balancers, and use the already implemented Neo4j AuraDB for database management. We could implement monitoring and logging using tools like CloudWatch. For evaluations we could use Arize or Langsmith.
2. Engineering standards you’ve followed (and maybe some that you skipped)
   - Followed standards: Modular code structure, containerization with Docker, use of version control (Git), comprehensive testing (unit, integration, contract, end to end, evaluations), and Spec driven documentation.
   - Skipped standards: Encryptions, authentications, extensive logging and monitoring.
3. How you used AI tools in your development process
   - Used Claude code for Research assistance, writing modules and testing.
   - Writing the comprehensive documentation (Not the README.md)
   - Generated Architecture diagram on README.md
4. What you'd do differently with more time
   - With more time, I would implement a more complex multi-agent workflow in LlamaIndex, and further optimize prompts based on evaluation feedback.
   - Better documentation on platform-based tools.
   - Optimise and refactor codebase for production readiness.
   - More comprehensive session management from frontend.
   - Persistent memory for sessions and agents.
   - Memory for agents to improve context retention.
   - Would implement Agent Lightning for a streamlined agent optimization automation pipeline

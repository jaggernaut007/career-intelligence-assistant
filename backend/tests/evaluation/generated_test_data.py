
# This file is automatically populated by generate_test_cases.py
# Do not edit manually unless you are moving cases to test_cases.py
from tests.evaluation.test_cases import AgentTestCase

NEW_CASES = []

# Generated for interview_prep
NEW_CASES = [
    AgentTestCase(
        id="interview_prep_gen_001",
        agent_name="interview_prep",
        input_data={
            "session_id": "sess_2026_01_31_001",
            "resume_id": "res_001",
            "job_id": "job_001",
            "skill_gaps": ["Kubernetes (EKS)", "Terraform", "Event-driven architecture (Kafka)"],
        },
        criteria=[
            "1. Output must be a dict that matches the InterviewPrepResult schema (session_id at top level).",
            "2. session_id must equal 'sess_2026_01_31_001' and questions must be a non-empty list.",
            "3. Each question must include: id (string), question (<=1000 chars), category in {behavioral, technical, situational, culture_fit}, difficulty in {easy, medium, hard}, and suggested_answer (<=3000 chars).",
            "4. The questions should reflect the job’s core requirements (AWS, Python, microservices, CI/CD, system design) and the resume’s experience (backend APIs, migrations, observability).",
            "5. At least 2 questions should directly probe the provided skill_gaps (Kubernetes/EKS, Terraform, Kafka/event-driven), and at least 1 of those should be difficulty='hard'.",
            "6. weakness_responses must be a non-empty list and include entries for at least two of the provided skill_gaps with both honest_response and mitigation populated.",
            "7. questions_to_ask must be a non-empty list and include at least one question about team processes (on-call, code review, incident response) and one about architecture/roadmap.",
            "8. talking_points must be a non-empty list and include quantified impact aligned to the resume (e.g., latency reduction, cost savings, reliability improvements).",
        ],
        description="Backend SWE -> Senior Backend Engineer (AWS microservices) with infra/eventing skill gaps",
        mock_data={
            "resumes": {
                "res_001": {
                    "id": "res_001",
                    "skills": [
                        "Python",
                        "FastAPI",
                        "Django",
                        "PostgreSQL",
                        "Redis",
                        "Docker",
                        "AWS (EC2, S3, RDS, CloudWatch)",
                        "CI/CD (GitHub Actions)",
                        "REST APIs",
                        "System design",
                        "Observability (Prometheus, Grafana)",
                    ],
                    "experiences": [
                        {
                            "title": "Backend Engineer",
                            "company": "FinTechCo",
                            "start_date": "2022-03",
                            "end_date": "2026-01",
                            "highlights": [
                                "Built and maintained Python microservices (FastAPI) handling ~15M requests/day.",
                                "Led migration from monolith to services; reduced p95 latency from 900ms to 350ms.",
                                "Implemented CI/CD with GitHub Actions; decreased deployment time from 45 min to 12 min.",
                                "Improved observability with Prometheus/Grafana and structured logging; cut MTTR by ~30%.",
                                "Worked with AWS RDS/Postgres tuning and caching strategies using Redis.",
                            ],
                        },
                        {
                            "title": "Software Engineer",
                            "company": "SaaSWorks",
                            "start_date": "2019-06",
                            "end_date": "2022-02",
                            "highlights": [
                                "Developed REST APIs and background jobs in Django; integrated third-party payment providers.",
                                "Designed database schema changes and performed zero-downtime migrations.",
                            ],
                        },
                    ],
                    "education": [
                        {
                            "degree": "B.S. Computer Science",
                            "institution": "State University",
                            "graduation_year": 2019,
                        }
                    ],
                }
            },
            "jobs": {
                "job_001": {
                    "id": "job_001",
                    "title": "Senior Backend Engineer (AWS)",
                    "required_skills": [
                        "Python",
                        "AWS",
                        "Microservices",
                        "Kubernetes (EKS)",
                        "Terraform",
                        "Kafka",
                        "PostgreSQL",
                        "CI/CD",
                        "System Design",
                        "Observability",
                    ],
                    "experience_years_min": 5,
                }
            },
        },
    ),
    AgentTestCase(
        id="interview_prep_gen_002",
        agent_name="interview_prep",
        input_data={
            "session_id": "sess_2026_01_31_002",
            "resume_id": "res_002",
            "job_id": "job_002",
            "skill_gaps": ["HIPAA compliance", "FHIR/HL7", "GCP (BigQuery)"],
        },
        criteria=[
            "1. Output must be a dict that matches the InterviewPrepResult schema (session_id at top level).",
            "2. session_id must equal 'sess_2026_01_31_002' and questions must be a non-empty list.",
            "3. The questions set must include a mix of categories (at least 3 distinct categories among behavioral, technical, situational, culture_fit).",
            "4. At least 2 questions must be healthcare-domain focused (data privacy/security, regulated environments, patient data handling) aligned to the job requirements.",
            "5. At least 2 questions must explicitly address the provided skill_gaps (HIPAA, FHIR/HL7, BigQuery/GCP), and weakness_responses must include those gaps with mitigation steps.",
            "6. Suggested answers must reference relevant resume experience (analytics pipelines, experimentation, stakeholder communication, metrics) and be plausible for a data/ML role.",
            "7. At least one InterviewQuestion should include a non-null star_example with situation/task/action/result all present and within schema limits.",
            "8. questions_to_ask must include at least one question about model monitoring/ML ops and one about data governance/security.",
        ],
        description="Data Scientist -> Healthcare Analytics DS (regulated data, FHIR, GCP) with domain/cloud gaps",
        mock_data={
            "resumes": {
                "res_002": {
                    "id": "res_002",
                    "skills": [
                        "Python",
                        "SQL",
                        "Pandas",
                        "scikit-learn",
                        "XGBoost",
                        "Statistics",
                        "A/B Testing",
                        "Airflow",
                        "dbt",
                        "Snowflake",
                        "Tableau",
                        "AWS (S3, Athena)",
                        "Data modeling",
                    ],
                    "experiences": [
                        {
                            "title": "Senior Data Scientist",
                            "company": "RetailPulse",
                            "start_date": "2021-01",
                            "end_date": "2026-01",
                            "highlights": [
                                "Built churn and propensity models (XGBoost) improving retention campaign ROI by 18%.",
                                "Designed experimentation framework and guardrail metrics; increased test velocity by ~40%.",
                                "Developed Airflow pipelines feeding Snowflake; improved data freshness from daily to hourly.",
                                "Partnered with product and engineering to define KPIs and instrument events.",
                            ],
                        },
                        {
                            "title": "Data Analyst",
                            "company": "MarketMetrics",
                            "start_date": "2018-07",
                            "end_date": "2020-12",
                            "highlights": [
                                "Created Tableau dashboards for executive reporting and cohort analysis.",
                                "Wrote complex SQL for customer segmentation and funnel diagnostics.",
                            ],
                        },
                    ],
                    "education": [
                        {
                            "degree": "M.S. Applied Statistics",
                            "institution": "Tech Institute",
                            "graduation_year": 2018,
                        }
                    ],
                }
            },
            "jobs": {
                "job_002": {
                    "id": "job_002",
                    "title": "Data Scientist, Healthcare Analytics",
                    "required_skills": [
                        "Python",
                        "SQL",
                        "Machine Learning",
                        "Causal inference / experimentation",
                        "Healthcare data (claims/EHR)",
                        "HIPAA compliance",
                        "FHIR/HL7",
                        "GCP (BigQuery)",
                        "Data pipelines",
                        "Model monitoring",
                    ],
                    "experience_years_min": 4,
                }
            },
        },
    ),
]

# Generated for recommendation
NEW_CASES += [
    AgentTestCase(
        id="recommendation_gen_001",
        agent_name="recommendation",
        description="Mid-level data analyst moving toward analytics engineering (SQL/dbt gaps)",
        input_data={
            "session_id": "sess_2026_01_31_001",
            "resume_id": "res_ana_001",
            "job_id": "job_ae_001",
            "skill_gaps": ["dbt", "Snowflake", "Airflow", "data modeling", "CI/CD for data pipelines"],
        },
        criteria=[
            "1. Output must conform to the RecommendationOutput schema and include recommendations.session_id matching the input session_id.",
            "2. recommendations.job_id should equal the input job_id (or be null only if the agent explicitly cannot resolve it).",
            "3. recommendations.recommendations must be a non-empty list with at least 4 items.",
            "4. Each recommendation must include: id, category (one of the allowed enums), priority (high/medium/low), title (<=200 chars), description (<=2000 chars).",
            "5. At least two recommendations must be category='skill_gap' addressing dbt and Snowflake (explicitly mentioned in either title, description, or action_items).",
            "6. At least one recommendation must be category='resume_improvement' OR category='experience_highlight' and must suggest concrete resume edits (e.g., add dbt project bullets, quantify impact).",
            "7. priority_order must list recommendation IDs and reflect descending priority (all 'high' before 'medium' before 'low').",
            "8. estimated_improvement, if provided, must be a number between 0 and 100.",
        ],
        mock_data={
            "resumes": {
                "res_ana_001": {
                    "id": "res_ana_001",
                    "skills": [
                        "SQL",
                        "Python",
                        "Tableau",
                        "Power BI",
                        "Excel",
                        "statistics",
                        "A/B testing",
                        "ETL (basic)",
                        "Git (basic)",
                    ],
                    "experiences": [
                        {
                            "title": "Data Analyst",
                            "company": "RetailCo",
                            "dates": "2022-03 to 2026-01",
                            "highlights": [
                                "Built Tableau dashboards for sales and inventory KPIs used by 40+ stakeholders.",
                                "Wrote SQL queries and Python scripts to automate weekly reporting (reduced manual effort by ~6 hours/week).",
                                "Partnered with engineering to define tracking for marketing attribution.",
                            ],
                        },
                        {
                            "title": "Business Analyst",
                            "company": "FinServe",
                            "dates": "2020-06 to 2022-02",
                            "highlights": [
                                "Created ad-hoc analyses for customer retention and churn drivers.",
                                "Maintained Excel-based forecasting models and presented findings to leadership.",
                            ],
                        },
                    ],
                    "education": [
                        {
                            "degree": "B.S. Economics",
                            "school": "State University",
                            "year": 2020,
                        }
                    ],
                }
            },
            "jobs": {
                "job_ae_001": {
                    "id": "job_ae_001",
                    "title": "Analytics Engineer (dbt + Snowflake)",
                    "required_skills": [
                        "SQL",
                        "dbt",
                        "Snowflake",
                        "data modeling",
                        "Airflow",
                        "Git",
                        "CI/CD",
                        "Python",
                    ],
                    "experience_years_min": 3,
                }
            },
        },
    ),
    AgentTestCase(
        id="recommendation_gen_002",
        agent_name="recommendation",
        description="Early-career backend engineer targeting cloud-native role (Kubernetes/Terraform gaps)",
        input_data={
            "session_id": "sess_2026_01_31_002",
            "resume_id": "res_be_002",
            "job_id": "job_swe_aws_002",
            "skill_gaps": ["Kubernetes", "Terraform", "AWS IAM", "observability (Prometheus/Grafana)", "system design"],
        },
        criteria=[
            "1. Output must conform to the RecommendationOutput schema and include recommendations.session_id matching the input session_id.",
            "2. recommendations.recommendations must contain between 3 and 7 items (inclusive).",
            "3. There must be at least one 'skill_gap' recommendation with high priority that addresses Kubernetes and Terraform (explicitly referenced).",
            "4. There must be at least one 'experience_highlight' OR 'resume_improvement' recommendation that instructs how to reframe existing work to match cloud-native/backend requirements.",
            "5. There must be at least one recommendation (of any category) that mentions 'certification' OR 'networking' OR 'AWS SAA' OR 'meetups' in its title, description, or action_items.",
            "6. Any recommendation that includes action_items must provide at least 3 concrete action items (e.g., build a project, add metrics, write a design doc).",
            "7. priority_order must include all recommendation IDs exactly once and be consistent with the stated priority levels.",
            "8. estimated_time values, if present, should be realistic strings (e.g., '1-2 weeks', '4-6 weeks') and not exceed 200 characters.",
        ],
        mock_data={
            "resumes": {
                "res_be_002": {
                    "id": "res_be_002",
                    "skills": [
                        "Java",
                        "Spring Boot",
                        "REST APIs",
                        "PostgreSQL",
                        "Redis",
                        "Docker",
                        "Git",
                        "CI (GitHub Actions)",
                        "unit testing",
                    ],
                    "experiences": [
                        {
                            "title": "Software Engineer I",
                            "company": "LogiShip",
                            "dates": "2024-07 to 2026-01",
                            "highlights": [
                                "Developed Spring Boot services for shipment tracking and notifications (avg 1.2k req/min peak).",
                                "Implemented Redis caching for rate-limited endpoints, reducing DB load by ~25%.",
                                "Containerized services with Docker and set up GitHub Actions pipelines for tests and builds.",
                            ],
                        },
                        {
                            "title": "Software Engineering Intern",
                            "company": "HealthTech Labs",
                            "dates": "2023-06 to 2023-08",
                            "highlights": [
                                "Added API endpoints and improved error handling/validation for patient scheduling module.",
                                "Wrote unit tests and improved coverage from 48% to 62% on a small service.",
                            ],
                        },
                    ],
                    "education": [
                        {
                            "degree": "B.S. Computer Science",
                            "school": "Metro University",
                            "year": 2024,
                        }
                    ],
                }
            },
            "jobs": {
                "job_swe_aws_002": {
                    "id": "job_swe_aws_002",
                    "title": "Backend Software Engineer (AWS, Kubernetes)",
                    "required_skills": [
                        "Java",
                        "AWS",
                        "Kubernetes",
                        "Terraform",
                        "microservices",
                        "PostgreSQL",
                        "observability",
                        "system design",
                        "CI/CD",
                    ],
                    "experience_years_min": 2,
                }
            },
        },
    ),
]

# Generated for market_insights
NEW_CASES += [
    AgentTestCase(
        id="market_insights_gen_001",
        agent_name="market_insights",
        input_data={
            "session_id": "sess_20260131_1001",
            "job_id": "job_ae_001",
            "job_title": "Analytics Engineer",
        },
        criteria=[
            "1. Output must be valid JSON-serializable and conform to the MarketInsightsResult schema (session_id at top level).",
            "2. session_id must exactly match input session_id ('sess_20260131_1001').",
            "3. job_id should equal the provided job_id ('job_ae_001') or be null, but must not be a different non-null value.",
            "4. insights.salary_range must include integer min/max/median >= 0, and median must be between min and max (inclusive).",
            "5. insights.demand_trend must be one of: 'increasing', 'stable', 'decreasing'.",
            "6. insights.industry_insights must be a non-empty string (<= 2000 chars) and discuss topics relevant to analytics engineering (data transformation, data pipelines, analytics tools, data modeling, business intelligence, or related concepts).",
            "7. If provided, top_skills_in_demand must be an array of strings and include at least three relevant skills (e.g., 'SQL', 'dbt', 'data modeling', 'Snowflake', 'BigQuery', 'Python', 'data pipelines').",
            "8. If provided, career_paths must be an array; each item must include 'title' (<=200 chars) and 'typical_years_to_reach' (0-30). Any 'salary_increase_percent' must be int 0-200 or null.",
            "9. data_freshness, if present, should be a string (ideally 'Based on Aug 2025 data' or similar).",
        ],
        description="Market insights for Analytics Engineer (modern data stack focus)",
        mock_data={
            "jobs": {
                "job_ae_001": {
                    "id": "job_ae_001",
                    "title": "Analytics Engineer",
                    "required_skills": [
                        "SQL",
                        "dbt",
                        "data modeling",
                        "Snowflake",
                        "Airflow",
                        "Looker",
                        "Git",
                    ],
                    "experience_years_min": 2,
                }
            }
        },
    ),
    AgentTestCase(
        id="market_insights_gen_002",
        agent_name="market_insights",
        input_data={
            "session_id": "sess_20260131_1002",
            "job_id": "job_gpm_014",
            "job_title": "Generative AI Product Manager",
        },
        criteria=[
            "1. Output must be valid JSON-serializable and conform to the MarketInsightsResult schema (session_id at top level).",
            "2. session_id must exactly match input session_id ('sess_20260131_1002').",
            "3. job_id should equal the provided job_id ('job_gpm_014') or be null, but must not be a different non-null value.",
            "4. insights.salary_range must include integer min/max/median >= 0, and median must be between min and max (inclusive).",
            "5. insights.demand_trend must be one of: 'increasing', 'stable', 'decreasing' and should be justified in industry_insights (e.g., adoption of LLMs, enterprise AI spend, regulation).",
            "6. insights.industry_insights must be a non-empty string (<= 2000 chars) and reference at least two of: LLMs, prompt engineering, RAG, model evaluation, AI governance, privacy/security.",
            "7. If provided, competitive_landscape must be a string (<= 1000 chars) or null; if string, it should mention competition for talent and/or cross-functional overlap (PM/ML/eng).",
            "8. If provided, top_skills_in_demand must be an array of strings and include at least three relevant skills (e.g., 'LLM product strategy', 'RAG', 'model evaluation', 'A/B testing', 'AI governance').",
            "9. If provided, career_paths must be an array; each item must include 'title' and 'typical_years_to_reach' (0-30).",
        ],
        description="Market insights for Generative AI Product Manager (LLM productization)",
        mock_data={
            "jobs": {
                "job_gpm_014": {
                    "id": "job_gpm_014",
                    "title": "Generative AI Product Manager",
                    "required_skills": [
                        "product management",
                        "LLM fundamentals",
                        "prompt engineering",
                        "RAG",
                        "model evaluation",
                        "A/B testing",
                        "AI governance",
                        "stakeholder management",
                    ],
                    "experience_years_min": 5,
                }
            }
        },
    ),
]

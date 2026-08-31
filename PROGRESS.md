# PROGRESS.md — Career Intelligence Assistant

## Current State
**Last Updated**: 2026-08-31
**Status**: GCP Cloud Run deployment DECOMMISSIONED (2026-08-31) — see ADR-008. Runs locally via Docker Compose only.

## What's Working
- Full backend with 8 AI agents (resume parser, JD analyzer, skill matcher, chat fit, interview prep, market insights, recommendation, chat)
- React frontend with wizard, chat, and results components
- Neo4j integration for graph + vector storage
- Docker Compose setup for local development
- Unit, integration, and contract test suites
- OpenAPI spec and agent contracts defined
- Cloud Run deployment with combined Dockerfile (nginx + uvicorn)
- GCP Secret Manager integration for all secrets
- Lazy-loaded ML models (sentence-transformers, Presidio/spaCy) to reduce startup memory
- PyTorch CPU-only build to reduce image size
- Deploy script (`deploy.sh`) with build, deploy, and health check

## What's In Progress
- Nothing currently in progress (Cloud Run instance-optimization work dropped — infra decommissioned 2026-08-31)

## What's Blocked
- Nothing currently blocked

## Next Steps
- [ ] Switch from local sentence-transformers to OpenAI embeddings API
- [ ] Remove Presidio/spaCy, keep regex-only PII detection
- [ ] Clean up requirements.txt (remove PyTorch, transformers, presidio)
- [ ] Shut down Neo4j AuraDB instance separately if no longer needed (hosted outside GCP)

## Recent Decisions
- Decommissioned the GCP Cloud Run deployment and project-specific infra; kept deploy files marked as decommissioned for historical reference (2026-08-31)
- Use `gpt-5.4-mini` as the default OpenAI model for better efficiency within current token budgets (2026-03-18)
- Min instances set to 0 for cost savings (scale to zero when idle) (2026-03-13)
- Plan to replace local embeddings with OpenAI API to eliminate PyTorch dependency (2026-03-13)
- Adopted agentic coding workflow per docs/agentic-guide-v2.md (2026-03-13)

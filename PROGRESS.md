# PROGRESS.md — Career Intelligence Assistant

## Current State
**Last Updated**: 2026-03-18
**Status**: Deployed to GCP Cloud Run, optimization planned

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
- Instance optimization to reduce Cloud Run specs from 4Gi/2CPU to ~1Gi/1CPU

## What's Blocked
- Nothing currently blocked

## Next Steps
- [ ] Switch from local sentence-transformers to OpenAI embeddings API
- [ ] Remove Presidio/spaCy, keep regex-only PII detection
- [ ] Clean up requirements.txt (remove PyTorch, transformers, presidio)
- [ ] Reduce Cloud Run specs and redeploy
- [ ] Verify health at lower specs

## Recent Decisions
- Use `gpt-5.4-mini` as the default OpenAI model for better efficiency within current token budgets (2026-03-18)
- Min instances set to 0 for cost savings (scale to zero when idle) (2026-03-13)
- Plan to replace local embeddings with OpenAI API to eliminate PyTorch dependency (2026-03-13)
- Adopted agentic coding workflow per docs/agentic-guide-v2.md (2026-03-13)

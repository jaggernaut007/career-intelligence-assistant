# ADR-008: GCP Cloud Run Serverless Deployment

## Status
Accepted

## Context
The application needs a production hosting solution that:
- Scales to zero when idle (cost control for a project that may have variable traffic)
- Auto-scales under load (parallel LLM API calls can spike CPU/memory)
- Supports Docker containers (both backend and frontend are containerized)
- Integrates with secret management (API keys for OpenAI, Neo4j, HuggingFace)
- Minimizes ops overhead (no Kubernetes cluster management)

## Decision
Deploy on GCP Cloud Run with the following configuration:

| Service | CPU | Memory | Scale Range | Estimated Cost |
|---------|-----|--------|-------------|----------------|
| Backend (FastAPI) | 2 vCPU | 2 GB | 0-10 instances | $10-50/month |
| Frontend (Nginx) | 1 vCPU | 512 MB | 0-5 instances | $5-20/month |

- **Secrets**: GCP Secret Manager for OPENAI_API_KEY, NEO4J_PASSWORD, HF_TOKEN, SESSION_SECRET_KEY
- **CI/CD**: Cloud Build triggers on `git push` to main; parallel build for backend + frontend
- **Registry**: GCP Artifact Registry for Docker images
- **CORS**: Backend configured with frontend Cloud Run URL

Alternatives considered:
- **AWS Lambda**: Cold start issues for FastAPI; WebSocket support requires API Gateway (complex)
- **Kubernetes (GKE)**: Full control, but over-engineered for this scale; $70+/month minimum
- **Vercel/Railway**: Simpler, but less control over scaling and secrets; Vercel is frontend-focused
- **Fly.io**: Good for containers, but less integrated with GCP Secret Manager

## Consequences
- **Easier**: Scale to zero saves money; Docker containers work as-is; Secret Manager is secure; Cloud Build automates deploys; no cluster management
- **Harder**: Cold starts add 2-5s latency on first request; 2GB memory limit may constrain large embedding model loads; Cloud Run has a 60-minute request timeout (sufficient but finite); debugging requires Cloud Logging integration

# GCP Cloud Run Deployment Guide

Deploy the Career Intelligence Assistant to Google Cloud Run for serverless, auto-scaling production hosting.

## Prerequisites

- [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) installed
- GCP project with billing enabled
- Docker installed locally
- Required API keys (OpenAI, Neo4j, HuggingFace)

## 1. GCP Project Setup

```bash
# Set your project ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com
```

## 2. Create Artifact Registry

```bash
# Create container registry
gcloud artifacts repositories create career-assistant \
    --repository-format=docker \
    --location=us-central1 \
    --description="Career Intelligence Assistant images"

# Configure Docker to use gcloud credentials
gcloud auth configure-docker us-central1-docker.pkg.dev
```

## 3. Store Secrets

```bash
# Create secrets for sensitive values
echo -n "sk-your-openai-key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your-neo4j-password" | gcloud secrets create neo4j-password --data-file=-
echo -n "hf_your-huggingface-token" | gcloud secrets create hf-token --data-file=-
echo -n "$(python -c 'import secrets; print(secrets.token_hex(32))')" | gcloud secrets create session-secret --data-file=-

# Grant Cloud Run access to secrets
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:$PROJECT_ID-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Repeat for other secrets...
```

## 4. Build and Push Backend

```bash
cd backend

# Build the image
docker build -t us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/backend:latest \
    --target production .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/backend:latest
```

## 5. Deploy Backend to Cloud Run

```bash
gcloud run deploy backend \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/backend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --min-instances 0 \
    --max-instances 10 \
    --set-env-vars "ENVIRONMENT=production,LOG_LEVEL=INFO" \
    --set-env-vars "NEO4J_URI=neo4j+s://xxx.databases.neo4j.io" \
    --set-env-vars "NEO4J_USERNAME=neo4j" \
    --set-env-vars "EMBEDDING_MODEL=nomic-ai/nomic-embed-text-v1.5" \
    --set-secrets "OPENAI_API_KEY=openai-api-key:latest" \
    --set-secrets "NEO4J_PASSWORD=neo4j-password:latest" \
    --set-secrets "HF_TOKEN=hf-token:latest" \
    --set-secrets "SESSION_SECRET_KEY=session-secret:latest"
```

## 6. Build and Push Frontend

```bash
cd frontend

# Build with production API URL
docker build \
    --build-arg VITE_API_URL=https://backend-xxx.run.app \
    -t us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/frontend:latest \
    --target production .

# Push to Artifact Registry
docker push us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/frontend:latest
```

## 7. Deploy Frontend to Cloud Run

```bash
gcloud run deploy frontend \
    --image us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/frontend:latest \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 512Mi \
    --cpu 1 \
    --timeout 60 \
    --concurrency 100 \
    --min-instances 0 \
    --max-instances 5
```

## 8. Configure CORS

Update backend with frontend URL:

```bash
gcloud run services update backend \
    --region us-central1 \
    --set-env-vars "CORS_ORIGINS=https://frontend-xxx.run.app"
```

## 9. Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service frontend \
    --domain your-domain.com \
    --region us-central1

# Verify domain ownership and update DNS
```

---

## CI/CD with Cloud Build

Create `cloudbuild.yaml` in project root:

```yaml
steps:
  # Build backend
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/backend:$COMMIT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/backend:latest'
      - '--target'
      - 'production'
      - './backend'

  # Build frontend
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/frontend:$COMMIT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/frontend:latest'
      - '--build-arg'
      - 'VITE_API_URL=${_BACKEND_URL}'
      - '--target'
      - 'production'
      - './frontend'

  # Push images
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '--all-tags', 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/backend']

  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', '--all-tags', 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/frontend']

  # Deploy backend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'backend'
      - '--image'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/backend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'

  # Deploy frontend
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'frontend'
      - '--image'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/frontend:$COMMIT_SHA'
      - '--region'
      - 'us-central1'

substitutions:
  _BACKEND_URL: 'https://backend-xxx.run.app'

images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/backend:$COMMIT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/career-assistant/frontend:$COMMIT_SHA'
```

### Set up Trigger

```bash
gcloud builds triggers create github \
    --name="deploy-on-push" \
    --repo-name="career-intelligence-assistant" \
    --repo-owner="your-github-username" \
    --branch-pattern="^main$" \
    --build-config="cloudbuild.yaml"
```

---

## Monitoring

### View Logs

```bash
# Backend logs
gcloud run services logs read backend --region us-central1

# Frontend logs
gcloud run services logs read frontend --region us-central1
```

### Set Up Alerts

```bash
# Create alert for high error rate
gcloud monitoring policies create \
    --display-name="High Error Rate - Backend" \
    --condition-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="backend" AND metric.type="run.googleapis.com/request_count" AND metric.labels.response_code_class="5xx"'
```

---

## Cost Optimization

1. **Set min-instances to 0** for scale-to-zero
2. **Use CPU throttling** for cost savings during idle
3. **Configure concurrency** appropriately (80 for backend, 100 for frontend)
4. **Use committed use discounts** for predictable workloads

### Estimated Costs

| Component | Specification | Est. Monthly Cost |
|-----------|--------------|-------------------|
| Backend | 2 vCPU, 2GB RAM, scale 0-10 | $10-50 |
| Frontend | 1 vCPU, 512MB RAM, scale 0-5 | $5-20 |
| Cloud Build | 120 min/day free | $0-5 |
| Secrets Manager | First 6 secrets free | $0 |

*Costs depend heavily on usage patterns.*

---

## Troubleshooting

### Container Won't Start

```bash
# Check container logs
gcloud run services logs read backend --region us-central1 --limit 50
```

### Connection Timeouts

- Increase `--timeout` to 300+ seconds for analysis endpoints
- Check Neo4j AuraDB allowlist includes Cloud Run IPs

### Memory Issues

- Increase `--memory` to 4Gi for heavy workloads
- Consider chunking large documents

### CORS Errors

- Verify `CORS_ORIGINS` includes exact frontend URL
- Check for protocol mismatches (http vs https)

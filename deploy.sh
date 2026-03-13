#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# Career Intelligence Assistant — Cloud Run Deployment Script
# ============================================================================

# --- Configuration ---
PROJECT_ID="career-intel-assistant"
REGION="europe-west2"
SERVICE_NAME="career-assistant"
REPO="career-assistant"
IMAGE_NAME="combined"
IMAGE="europe-west2-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE_NAME}:latest"
SERVICE_ACCOUNT="973476355791-compute@developer.gserviceaccount.com"

# --- Resource Settings ---
MEMORY="4Gi"
CPU="2"
MIN_INSTANCES="0"

# --- Environment Variables ---
OPENAI_MODEL="gpt-5-mini"
ENVIRONMENT="production"

# --- Secrets (from GCP Secret Manager) ---
SECRETS=(
  "OPENAI_API_KEY=OPENAI_API_KEY:latest"
  "APP_PASSWORD=APP_PASSWORD:latest"
  "NEO4J_URI=NEO4J_URI:latest"
  "NEO4J_USERNAME=NEO4J_USERNAME:latest"
  "NEO4J_PASSWORD=NEO4J_PASSWORD:latest"
)

# ============================================================================
# Helper functions
# ============================================================================

log() { echo "==> $*"; }
err() { echo "ERROR: $*" >&2; exit 1; }

join_by() {
  local sep="$1"; shift
  local first="$1"; shift
  printf '%s' "$first" "${@/#/$sep}"
}

# ============================================================================
# Parse arguments
# ============================================================================

BUILD_ONLY=false
DEPLOY_ONLY=false
SKIP_CONFIRM=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --build-only)  BUILD_ONLY=true; shift ;;
    --deploy-only) DEPLOY_ONLY=true; shift ;;
    --yes|-y)      SKIP_CONFIRM=true; shift ;;
    --help|-h)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  --build-only   Only build and push the image (skip deploy)"
      echo "  --deploy-only  Only deploy (skip build, use existing image)"
      echo "  --yes, -y      Skip confirmation prompt"
      echo "  --help, -h     Show this help"
      exit 0
      ;;
    *) err "Unknown option: $1" ;;
  esac
done

# ============================================================================
# Pre-flight checks
# ============================================================================

log "Checking gcloud authentication..."
gcloud auth print-access-token > /dev/null 2>&1 || err "Not authenticated. Run: gcloud auth login"

log "Project:  ${PROJECT_ID}"
log "Region:   ${REGION}"
log "Service:  ${SERVICE_NAME}"
log "Image:    ${IMAGE}"
log "Memory:   ${MEMORY} | CPU: ${CPU} | Min instances: ${MIN_INSTANCES}"
log "Model:    ${OPENAI_MODEL}"

if [[ "$SKIP_CONFIRM" != "true" ]]; then
  read -rp "Proceed? [y/N] " confirm
  [[ "$confirm" =~ ^[Yy]$ ]] || { echo "Aborted."; exit 0; }
fi

# ============================================================================
# Step 1: Build image via Cloud Build
# ============================================================================

if [[ "$DEPLOY_ONLY" != "true" ]]; then
  log "Submitting build to Cloud Build..."
  gcloud builds submit \
    --config cloudbuild.yaml \
    --project "${PROJECT_ID}" \
    --quiet

  log "Build complete."
fi

# ============================================================================
# Step 2: Ensure secret IAM bindings
# ============================================================================

log "Ensuring secret access for service account..."
for entry in "${SECRETS[@]}"; do
  secret_name="${entry%%=*}"
  gcloud secrets add-iam-policy-binding "${secret_name}" \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --project="${PROJECT_ID}" \
    --quiet > /dev/null 2>&1 || true
done
log "Secret IAM bindings verified."

# ============================================================================
# Step 3: Deploy to Cloud Run
# ============================================================================

if [[ "$BUILD_ONLY" != "true" ]]; then
  SECRETS_FLAG=$(join_by "," "${SECRETS[@]}")

  log "Deploying to Cloud Run..."
  gcloud run deploy "${SERVICE_NAME}" \
    --image "${IMAGE}" \
    --region "${REGION}" \
    --platform managed \
    --memory "${MEMORY}" \
    --cpu "${CPU}" \
    --min-instances "${MIN_INSTANCES}" \
    --cpu-boost \
    --port 8080 \
    --allow-unauthenticated \
    --set-secrets="${SECRETS_FLAG}" \
    --set-env-vars="OPENAI_MODEL=${OPENAI_MODEL},ENVIRONMENT=${ENVIRONMENT}" \
    --project "${PROJECT_ID}"

  log "Deployment complete."
fi

# ============================================================================
# Step 4: Verify
# ============================================================================

if [[ "$BUILD_ONLY" != "true" ]]; then
  SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
    --region "${REGION}" \
    --project "${PROJECT_ID}" \
    --format="value(status.url)")

  log "Service URL: ${SERVICE_URL}"

  log "Health check..."
  HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}/")
  if [[ "$HTTP_CODE" == "200" ]]; then
    log "Service is healthy (HTTP ${HTTP_CODE})"
  else
    err "Service returned HTTP ${HTTP_CODE} — check logs: gcloud run logs read ${SERVICE_NAME} --region ${REGION} --project ${PROJECT_ID}"
  fi
fi

log "Done."

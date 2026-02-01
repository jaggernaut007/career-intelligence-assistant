# Environment Variables Reference

Complete reference for all environment variables used by the Career Intelligence Assistant.

## Required Variables

These must be set for the application to function.

### OpenAI Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT-5.2 |
| `OPENAI_MODEL` | No | `gpt-5.2` | OpenAI model to use |

### Neo4j Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEO4J_URI` | Yes | - | Neo4j connection URI (e.g., `neo4j+s://xxx.databases.neo4j.io`) |
| `NEO4J_USERNAME` | No | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | Yes | - | Neo4j password |

### HuggingFace Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HF_TOKEN` | Yes | - | HuggingFace API token for embeddings |
| `EMBEDDING_MODEL` | No | `nomic-ai/nomic-embed-text-v1.5` | Embedding model name |
| `EMBEDDING_DIMENSION` | No | `768` | Embedding vector dimension |

## Optional Variables

### Server Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `HOST` | No | `0.0.0.0` | Server host address |
| `PORT` | No | `8000` | Server port |

### Application Settings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SESSION_SECRET_KEY` | No | `dev-secret-key...` | Secret key for session encryption. **Change in production!** |
| `RATE_LIMIT_PER_MINUTE` | No | `10` | API rate limit per session per minute |
| `MAX_FILE_SIZE_MB` | No | `10` | Maximum upload file size in MB |
| `MAX_CONTENT_LENGTH` | No | `50000` | Maximum content length in characters |
| `MAX_JOBS_PER_SESSION` | No | `5` | Maximum job descriptions per session |

### CORS and Security

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CORS_ORIGINS` | No | `http://localhost:5173,http://localhost:3000` | Comma-separated allowed origins |
| `ENVIRONMENT` | No | `development` | Environment name (`development` or `production`) |
| `LOG_LEVEL` | No | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

### LlamaIndex Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLAMAINDEX_CHUNK_SIZE` | No | `512` | Text chunk size for document processing |
| `LLAMAINDEX_CHUNK_OVERLAP` | No | `50` | Overlap between text chunks |
| `VECTOR_SIMILARITY_THRESHOLD` | No | `0.75` | Minimum similarity for semantic matching |
| `NEO4J_VECTOR_INDEX_NAME` | No | `career_vectors` | Neo4j vector index name |

## Example .env File

```ini
# =============================================================================
# OpenAI Configuration
# =============================================================================
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_MODEL=gpt-5.2

# =============================================================================
# Neo4j AuraDB Configuration
# Get free instance at: https://console.neo4j.io/
# =============================================================================
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password-here

# =============================================================================
# HuggingFace Configuration
# Get token at: https://huggingface.co/settings/tokens
# =============================================================================
HF_TOKEN=hf_your-token-here

# =============================================================================
# Application Configuration
# =============================================================================
SESSION_SECRET_KEY=change-this-to-a-random-secret-key-in-production
RATE_LIMIT_PER_MINUTE=10
MAX_FILE_SIZE_MB=10
MAX_JOBS_PER_SESSION=5

# =============================================================================
# CORS (add your frontend URL in production)
# =============================================================================
CORS_ORIGINS=http://localhost:5173,http://localhost:3000

# =============================================================================
# Environment
# =============================================================================
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## Production Recommendations

1. **Generate secure session key**:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Set environment to production**:
   ```ini
   ENVIRONMENT=production
   ```

3. **Restrict CORS origins**:
   ```ini
   CORS_ORIGINS=https://your-frontend-domain.com
   ```

4. **Use secret management** (GCP Secret Manager, AWS Secrets Manager, etc.) instead of `.env` files in production.

## GCP Cloud Run Configuration

When deploying to Cloud Run, set these as environment variables or secrets:

```bash
# Set via gcloud CLI
gcloud run services update backend \
  --set-env-vars="ENVIRONMENT=production,LOG_LEVEL=INFO" \
  --set-secrets="OPENAI_API_KEY=openai-key:latest,NEO4J_PASSWORD=neo4j-password:latest"
```

See [GCP Cloud Run Deployment](gcp-cloud-run.md) for detailed instructions.

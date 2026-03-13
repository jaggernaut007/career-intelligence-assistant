# TODO — Instance Optimization

Goal: Reduce Cloud Run memory/CPU requirements from 4Gi/2CPU to ~1Gi/1CPU.

## Tasks

- [ ] Switch from local sentence-transformers to OpenAI embeddings API
  - Eliminates PyTorch + sentence-transformers (~2Gi savings)
  - Use `text-embedding-3-small` via existing OpenAI API key
  - Update `EmbeddingService` in `backend/app/services/embedding.py`

- [ ] Remove Presidio/spaCy, keep regex-only PII detection
  - Fallback regex patterns already cover SSNs, phones, emails
  - Remove Presidio initialization from `backend/app/guardrails/pii_detector.py`
  - ~500MB savings

- [ ] Clean up requirements.txt
  - Remove: `torch`, `sentence-transformers`, `transformers`, `einops`
  - Remove: `presidio-analyzer`, `presidio-anonymizer`
  - Remove: `--extra-index-url` for PyTorch CPU
  - Keep: `openai` (already present)

- [ ] Reduce Cloud Run instance specs
  - Memory: 4Gi → 1Gi
  - CPU: 2 → 1
  - Update `deploy.sh` with new specs

- [ ] Rebuild and deploy optimized image
  - Smaller Docker image (no PyTorch layer)
  - Verify health check passes at lower specs

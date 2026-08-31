# TODO — Instance Optimization

> **Note (2026-08-31):** The GCP Cloud Run deployment has been **decommissioned**
> (see ADR-008). The Cloud Run–specific tasks below (spec reduction, rebuild &
> deploy) no longer apply. The dependency-slimming tasks are still worthwhile for
> local Docker Compose runs and any future hosting.

Goal (historical): Reduce Cloud Run memory/CPU requirements from 4Gi/2CPU to ~1Gi/1CPU.

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

- [x] ~~Reduce Cloud Run instance specs~~ — N/A, Cloud Run infra decommissioned 2026-08-31

- [x] ~~Rebuild and deploy optimized image~~ — N/A, Cloud Run infra decommissioned 2026-08-31

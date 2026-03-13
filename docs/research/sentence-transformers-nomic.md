# Research: Sentence Transformers + Nomic Embeddings Stack
**Library versions (pinned in project):**
- `sentence-transformers>=2.3.1`
- `transformers>=4.37.2`
- `torch>=2.2.0`
- Model: `nomic-ai/nomic-embed-text-v1.5`

**Latest available (March 2026):**
- `sentence-transformers` 5.3.0 (Apache 2.0) — requires Python >=3.10
- `transformers` 5.3.0 (Apache 2.0)
- `torch` 2.10.0 (BSD-3-Clause)

**Status:** Needs update — all three packages have had major version bumps since pinned versions.

## Sources Consulted
| Source | URL | Date accessed |
|--------|-----|---------------|
| PyPI — sentence-transformers | https://pypi.org/project/sentence-transformers/ | 2026-03-13 |
| PyPI — transformers | https://pypi.org/project/transformers/ | 2026-03-13 |
| PyPI — torch | https://pypi.org/project/torch/ | 2026-03-13 |
| HuggingFace Model Card — nomic-embed-text-v1.5 | https://huggingface.co/nomic-ai/nomic-embed-text-v1.5 | 2026-03-13 |
| GitHub — sentence-transformers | https://github.com/UKPLab/sentence-transformers | 2026-03-13 |
| GitHub — Nomic AI | https://github.com/nomic-ai | 2026-03-13 |

## The Correct Approach

The project uses Nomic embeddings via `sentence-transformers` with HuggingFace authentication (`HF_TOKEN`). The correct usage pattern:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer(
    "nomic-ai/nomic-embed-text-v1.5",
    trust_remote_code=True  # REQUIRED — Nomic uses custom code
)

# CRITICAL: Must prefix text with task type
doc_embeddings = model.encode(["search_document: " + text for text in documents])
query_embedding = model.encode(["search_query: " + query])
```

Key correct decisions in this project:
- Using `trust_remote_code=True` (mandatory for Nomic)
- Using cosine similarity (matches model training objective)
- 768-dim output (full fidelity, though model supports Matryoshka truncation down to 64-dim)
- 8k context window (requires `rotary_scaling_factor=2` for sequences > 2048 tokens)
- HF_TOKEN for authenticated model downloads

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|----------|-------------|
| OpenAI `text-embedding-3-small` | Adds per-token API cost; vendor lock-in; data leaves infrastructure |
| `nomic-embed-text-v1` (original) | v1.5 adds Matryoshka dimensionality, better MTEB scores, vision alignment |
| ONNX/quantized Nomic variant | Added complexity; CPU-only inference is fast enough for batch resume processing |
| `all-MiniLM-L6-v2` (384-dim) | Lower quality embeddings; Nomic outperforms on MTEB across all dimensions |
| Direct `transformers` AutoModel usage | `sentence-transformers` handles pooling, normalization, and batching automatically |
| Cohere/Voyage embeddings API | Same cost/vendor-lock concerns as OpenAI embeddings |

## Security Assessment
- [x] CVE check
  - **sentence-transformers**: No known CVEs as of March 2026. The `trust_remote_code=True` parameter is an inherent security concern — it executes arbitrary Python from the model repo. Mitigated by pinning to a known-good model revision.
  - **transformers**: Historically had deserialization vulnerabilities with pickle-based model loading (CVE-2023-7018, CVE-2024-3568 relating to `torch.load` with arbitrary code execution). Newer versions default to `safetensors` format. Ensure the Nomic model is loaded via safetensors, not pickle.
  - **torch**: CVE-2024-48063 (arbitrary code execution via `torch.load` without `weights_only=True`). Fixed in torch >= 2.4. The pinned version (>=2.2.0) is vulnerable — update recommended.
  - **Model supply chain**: The `nomic-ai/nomic-embed-text-v1.5` model repo on HuggingFace could theoretically be compromised. Pin the model revision hash for production.
- [x] Maintenance health
  - **sentence-transformers**: Very actively maintained by UKP Lab (TU Darmstadt). ~15k GitHub stars. Regular releases. Strong bus factor (multiple maintainers + Hugging Face backing).
  - **transformers**: Flagship Hugging Face library. 140k+ GitHub stars. Extremely active. Excellent maintenance.
  - **torch**: Meta/PyTorch Foundation. One of the most actively maintained ML libraries. Excellent maintenance.
  - **Nomic model**: 8.1M+ downloads/month, 780 likes on HuggingFace. Nomic AI is a funded company. 28 finetunes, 25 quantizations available. Vision counterpart (`nomic-embed-vision-v1.5`) extends the ecosystem.
- [x] License compatibility
  - sentence-transformers: **Apache 2.0** — permissive, compatible
  - transformers: **Apache 2.0** — permissive, compatible
  - torch: **BSD-3-Clause** — permissive, compatible
  - Nomic model: **Apache 2.0** — permissive, compatible
  - All licenses are mutually compatible and business-friendly.
- [x] Dependency tree risk
  - `torch` is the heaviest dependency (~2GB+ installed). Pulls in CUDA/MKL/MPS backends.
  - `sentence-transformers` depends on `transformers`, `torch`, `huggingface-hub`, `scipy`, `scikit-learn`, `Pillow`, `tqdm`.
  - `transformers` pulls in `tokenizers` (Rust-backed), `safetensors`, `regex`, `requests`, `numpy`.
  - Deep dependency tree but all from well-maintained, high-trust sources.

## Known Gotchas / Edge Cases

### 1. Task Prefix is MANDATORY (Critical)
The Nomic model **requires** task instruction prefixes on all input text:
- `search_document:` for documents being indexed
- `search_query:` for queries at search time
- `clustering:` for clustering tasks
- `classification:` for classification tasks

**If you omit the prefix, embeddings will be low quality and retrieval will fail silently** — no error is raised.

### 2. `trust_remote_code=True` is Required
Nomic uses custom modeling code hosted on HuggingFace. Without `trust_remote_code=True`, loading will fail with an error about unrecognized model architecture.

### 3. Torch CPU vs GPU
- **CPU inference** works fine for batch processing (resume parsing). Expect ~50-200ms per document depending on length.
- **GPU (CUDA)** provides 10-50x speedup for batch embedding. Worth it if processing many resumes concurrently.
- **MPS (Apple Silicon)** supported in torch >= 2.2.0 but can have numerical precision differences with float16. Stick to float32 on MPS.
- **Memory**: CPU mode uses ~500MB RAM for the model. GPU mode uses ~500MB VRAM.

### 4. Model Download Size
- First load downloads ~550MB from HuggingFace (model weights + tokenizer + config).
- Cached in `~/.cache/huggingface/hub/` — ensure disk space in containerized deployments.
- `HF_TOKEN` is required for gated model access. If the token is missing or expired, download fails with a cryptic 401 error.

### 5. Long Context (> 2048 tokens)
The model's base context is 2048 tokens. For the full 8192-token context:
```python
model = AutoModel.from_pretrained(
    'nomic-ai/nomic-embed-text-v1.5',
    trust_remote_code=True,
    rotary_scaling_factor=2  # Enables 8k context
)
```
When using `SentenceTransformer` wrapper, verify that the rotary scaling is passed through correctly. Resumes rarely exceed 2048 tokens, but combined multi-section documents might.

### 6. Breaking Changes Since Pinned Versions

**sentence-transformers 2.3.1 to 5.3.0:**
- Major API overhaul in v3.0 (mid-2024): new training API, `SentenceTransformerTrainer` replaced `SentenceTransformer.fit()`.
- `encode()` interface remains stable — inference code likely unaffected.
- Python 3.10+ required (was 3.8+). Verify project Python version.

**transformers 4.37.2 to 5.3.0:**
- v5.0 was a major release with breaking changes to model loading internals.
- `safetensors` became the default serialization format.
- Many deprecated APIs removed.
- AutoModel inference code pattern is stable — likely unaffected.

**torch 2.2.0 to 2.10.0:**
- `torch.load()` now defaults to `weights_only=True` (security fix).
- `torch.compile()` matured significantly.
- New `torch.export` API.
- Basic tensor operations and model inference are backward-compatible.

### 7. Matryoshka Dimensionality (Optimization Opportunity)
The model supports truncating embeddings from 768 to 512, 256, 128, or 64 dimensions with minimal quality loss:
- 768-dim: MTEB 62.28
- 256-dim: MTEB 61.04 (1.2 point loss, 3x storage savings)

If vector storage becomes a bottleneck, consider truncation with proper normalization:
```python
import torch.nn.functional as F
embeddings = F.layer_norm(embeddings, normalized_shape=(embeddings.shape[1],))
embeddings = embeddings[:, :256]
embeddings = F.normalize(embeddings, p=2, dim=1)
```

### 8. HuggingFace Hub Rate Limits
Unauthenticated requests to HuggingFace are rate-limited. In CI/CD or multi-container deployments, share the model cache volume or pre-download the model to avoid repeated downloads and rate limit hits.

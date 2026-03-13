# Research: Microsoft Presidio (presidio-analyzer / presidio-anonymizer)
**Library version (pinned in project):** `presidio-analyzer>=2.2.354`, `presidio-anonymizer>=2.2.354`
**Latest available:** 2.2.361 (fetched from PyPI, March 2026)
**Status:** Needs update (minor patch versions behind; no breaking changes expected)

## Sources Consulted
| Source | URL | Date accessed |
|---|---|---|
| PyPI - presidio-analyzer | https://pypi.org/project/presidio-analyzer/ | 2026-03-13 |
| PyPI - presidio-anonymizer | https://pypi.org/project/presidio-anonymizer/ | 2026-03-13 |
| GitHub - microsoft/presidio | https://github.com/microsoft/presidio | 2026-03-13 |
| Presidio Documentation | https://microsoft.github.io/presidio/ | 2026-03-13 |
| NVD / CVE Database | https://nvd.nist.gov/ | 2026-03-13 |

## The Correct Approach
The project uses Presidio for PII detection (SSN, email, phone, addresses) with spaCy NER and regex fallback. This is the standard and recommended usage pattern:

```python
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine

# Initialize with spaCy NER model
analyzer = AnalyzerEngine()  # defaults to en_core_web_lg spaCy model

# Detect PII entities
results = analyzer.analyze(
    text="My SSN is 123-45-6789 and email is john@example.com",
    entities=["US_SSN", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION"],
    language="en"
)

# Anonymize detected PII
anonymizer = AnonymizerEngine()
anonymized = anonymizer.anonymize(text=text, analyzer_results=results)
```

Key patterns used correctly in this project:
- **Entity-specific detection**: Specifying exact entity types (`US_SSN`, `EMAIL_ADDRESS`, `PHONE_NUMBER`) rather than detecting all entities reduces false positives.
- **spaCy NER + regex fallback**: Presidio's built-in recognizers use regex for structured patterns (SSN, email, phone) and spaCy NER for unstructured entities (names, addresses). This dual approach is the recommended pattern.
- **Minimum version pinning with `>=`**: Allows automatic pickup of patch-level fixes while guarding against regressions from older versions.

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|---|---|
| AWS Comprehend PII Detection | Vendor lock-in; per-request cost at scale; data leaves the application boundary |
| Google Cloud DLP | Same vendor lock-in and cost concerns; heavier integration overhead |
| Custom regex-only PII detection | Misses context-dependent PII (names, addresses); high false-negative rate for unstructured text |
| spaCy NER alone (without Presidio) | No built-in PII entity taxonomy; would require building recognizer framework from scratch |
| Presidio with Stanza or Transformers NER | Heavier model downloads; slower inference; spaCy offers best balance of speed and accuracy for this use case |
| `presidio-image-redactor` | Not needed -- project only processes text, not images |

## Security Assessment
- [x] CVE check
  - No known CVEs filed directly against `presidio-analyzer` or `presidio-anonymizer` as of March 2026.
  - Transitive dependency risk: spaCy and its dependencies (thinc, numpy, etc.) have had occasional CVEs. Pin spaCy version and monitor advisories.
  - Presidio does not execute user-supplied code or deserialize untrusted data in standard usage, reducing attack surface.
- [x] Maintenance health (last release, open issues, bus factor)
  - **Last release**: 2.2.361 on PyPI (active development through 2025-2026).
  - **Release cadence**: Approximately monthly patch releases in the 2.2.3xx series. Microsoft maintains this as part of their compliance/privacy tooling portfolio.
  - **GitHub stats**: ~3,000+ stars, 400+ forks. Active issue triage and PR review.
  - **Bus factor**: Backed by Microsoft; multiple maintainers from Microsoft's Cloud + AI division. Low abandonment risk.
  - **Open issues**: Typically 50-100 open issues; most are feature requests or edge-case entity recognition improvements.
- [x] License compatibility
  - **MIT License** (confirmed via GitHub repository and PyPI classifiers).
  - Fully compatible with commercial and open-source use. No copyleft obligations.
- [x] Dependency tree risk
  - Key dependencies: `spacy`, `regex`, `tldextract`, `pyyaml`, `phonenumbers`.
  - `spacy` is the heaviest dependency (~200MB with model). It in turn depends on `thinc`, `numpy`, `cymem`, `preshed`.
  - All dependencies are well-maintained, widely used libraries.
  - **Risk**: spaCy model downloads (`en_core_web_lg`, ~560MB) require internet access at install/build time. Must be handled in CI/CD and Docker builds.

## Known Gotchas / Edge Cases

### 1. spaCy Model Downloads
- Presidio requires a spaCy language model (typically `en_core_web_lg`) to be downloaded separately.
- **Gotcha**: `pip install presidio-analyzer` does NOT install the spaCy model. You must run:
  ```bash
  python -m spacy download en_core_web_lg
  ```
- In Docker builds, add this as a separate `RUN` step. In CI, cache the model to avoid re-downloading on every build.
- If the model is missing at runtime, you get a cryptic `OSError` from spaCy, not a helpful Presidio error.
- **Mitigation**: Add a startup health check that verifies `spacy.load("en_core_web_lg")` succeeds.

### 2. False Positive Rates
- **Phone numbers**: Presidio's phone number recognizer can flag sequences of digits that are not phone numbers (e.g., order IDs, zip codes). Tune the `score_threshold` (default 0.0; recommend 0.4+).
- **Names**: spaCy NER can misidentify common nouns as person names, especially in domain-specific text (e.g., "Java" as a location, "Spring" as a person). Use `entities` parameter to restrict detection to needed types.
- **Addresses**: US address detection relies on spaCy's `LOC`/`GPE` entities which have moderate recall. Consider adding custom recognizers for structured address patterns.
- **SSN**: Regex-based; very reliable for formatted SSNs (XXX-XX-XXXX) but may miss unformatted 9-digit sequences or flag similar patterns.

### 3. Async Usage
- **Presidio is synchronous.** `AnalyzerEngine.analyze()` and `AnonymizerEngine.anonymize()` are blocking calls.
- In a FastAPI/async context, wrap calls in `asyncio.to_thread()` or use a thread pool executor:
  ```python
  import asyncio
  result = await asyncio.to_thread(analyzer.analyze, text=text, language="en", entities=entities)
  ```
- Do NOT call `analyzer.analyze()` directly in an `async def` endpoint -- it will block the event loop.
- The `AnalyzerEngine` is thread-safe for concurrent reads (analysis). Safe to share a single instance across threads.

### 4. Breaking Changes Since 2.2.354
- The 2.2.354 to 2.2.361 range is patch-level updates. No breaking API changes have been introduced.
- Notable improvements in this range:
  - Improved entity recognition accuracy for phone numbers and addresses.
  - Bug fixes for edge cases in overlapping entity detection.
  - Updated supported Python versions: dropped Python 3.8/3.9 support, added Python 3.12/3.13 support. Requires `>=3.10,<3.14`.
- **Action**: If the project currently runs on Python 3.9 or below, upgrading Presidio past ~2.2.356 will require upgrading Python to 3.10+.

### 5. Custom Recognizer Registration
- When adding custom recognizers (e.g., for employee IDs or custom PII patterns), register them before creating the `AnalyzerEngine`, or use `registry.add_recognizer()` followed by creating a new engine instance.
- Custom recognizers added after engine initialization may not be picked up in all code paths.

### 6. Performance Considerations
- First call to `analyzer.analyze()` is slow (~2-5 seconds) because it loads the spaCy model lazily. Subsequent calls are fast (~10-50ms for short texts).
- For batch processing, reuse the same `AnalyzerEngine` instance. Do not create a new one per request.
- For very large texts (>10KB), consider chunking the text to avoid memory spikes from spaCy's NER pipeline.

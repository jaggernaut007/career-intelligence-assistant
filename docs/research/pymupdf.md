# Research: PyMuPDF
**Library version (pinned in project):** `pymupdf>=1.23.22`
**Latest available (March 2026):** 1.27.2
**Status:** Needs update — multiple minor versions behind. License change occurred (AGPL 3.0).

## Sources Consulted
| Source | URL | Date accessed |
|--------|-----|---------------|
| PyPI — PyMuPDF | https://pypi.org/project/PyMuPDF/ | 2026-03-13 |
| GitHub — PyMuPDF | https://github.com/pymupdf/PyMuPDF | 2026-03-13 |
| Artifex Software (upstream MuPDF) | https://mupdf.com/ | 2026-03-13 |
| NVD — CVE Database | https://nvd.nist.gov/ | 2026-03-13 |
| PyMuPDF Changelog | https://pymupdf.readthedocs.io/en/latest/changes.html | 2026-03-13 |

## The Correct Approach

The project uses PyMuPDF for PDF resume parsing alongside `python-docx` for DOCX files. The correct pattern:

```python
import pymupdf  # Note: import name changed from 'fitz' to 'pymupdf' in v1.24.0+

def extract_text_from_pdf(file_path: str) -> str:
    doc = pymupdf.open(file_path)
    try:
        text = ""
        for page in doc:
            text += page.get_text("text")  # Plain text extraction
        return text
    finally:
        doc.close()
```

Key correct decisions:
- Using PyMuPDF over alternatives (fastest Python PDF text extractor by benchmarks)
- Paired with `python-docx` (MIT, v1.2.0 latest) for DOCX support — covers the two primary resume formats
- Text extraction mode (`"text"`) is appropriate for resumes (vs. `"html"`, `"dict"`, `"rawdict"`)

## What We Ruled Out (and Why)
| Approach | Why Rejected |
|----------|-------------|
| `pdfplumber` | Slower than PyMuPDF (5-10x). Better for tables but resumes are primarily text. |
| `PyPDF2` / `pypdf` | Significantly worse text extraction quality, especially for multi-column layouts and special characters. |
| `pdfminer.six` | Slower, more complex API. Better for layout analysis but overkill for resume text extraction. |
| Apache Tika (via `tika-python`) | Requires JVM runtime. Heavy dependency for a simple text extraction task. |
| `unstructured` library | Heavy dependency tree (installs many backends). Overkill when only PDF/DOCX support needed. |
| Cloud-based OCR (Google Vision, AWS Textract) | Adds latency, cost, and data-leaves-infrastructure concerns. Most resumes are text-based PDFs, not scanned images. |

## Security Assessment
- [x] CVE check
  - **PyMuPDF wraps MuPDF (C library) — PDF parsing is a known high-risk attack surface.**
  - MuPDF has had multiple CVEs historically:
    - CVE-2023-31794: Stack buffer overflow in MuPDF via crafted PDF (fixed in MuPDF 1.22.x)
    - CVE-2023-38560: Heap buffer overflow in MuPDF's `pdf_load_page_tree` (fixed in MuPDF 1.23.x)
    - CVE-2024-46295, CVE-2024-46296, CVE-2024-46297: Multiple buffer overflows in MuPDF 1.24.x (fixed in 1.24.9+)
  - **The pinned version (>=1.23.22) is vulnerable to the 2024 CVEs.** Updating to >=1.25.x is recommended.
  - PDF files uploaded by users should be treated as untrusted input. Consider:
    - File size limits (prevent memory exhaustion)
    - Timeout on extraction (prevent CPU exhaustion from malicious PDFs)
    - Running extraction in a sandboxed subprocess or container
    - Validating file magic bytes before processing (project already has `python-magic` and `puremagic`)
- [x] Maintenance health
  - **Actively maintained** by Artifex Software (commercial company behind MuPDF/Ghostscript).
  - Regular releases — multiple releases per quarter.
  - Strong community: well-documented, responsive issue tracker.
  - Backed by a commercial entity — low bus-factor risk.
  - The `pymupdf` package on PyPI has high download counts (millions/month).
- [x] License compatibility
  - **CRITICAL LICENSE CHANGE**: PyMuPDF is now dual-licensed:
    - **GNU Affero General Public License v3.0 (AGPL-3.0)** — copyleft, requires source disclosure for network services
    - **Artifex Commercial License** — paid, proprietary-friendly
  - The AGPL-3.0 license is **viral for web services**: if the project serves users over a network (which it does — FastAPI backend), the entire application source code must be made available under AGPL-3.0 or a compatible license.
  - **This is a significant legal concern.** Options:
    1. Purchase an Artifex commercial license
    2. Switch to an alternative library (`pypdf` is BSD-licensed but lower quality)
    3. Ensure the project's license is AGPL-3.0 compatible
    4. Isolate PyMuPDF in a separate microservice with its own AGPL-compliant source disclosure
  - Previous versions (pre-1.24.x era) were under a more permissive license. The project may have been set up before the license change.
- [x] Dependency tree risk
  - PyMuPDF bundles MuPDF as a compiled C extension — no separate MuPDF install needed.
  - Minimal Python dependencies (essentially standalone).
  - Binary wheels available for major platforms (Linux, macOS, Windows).
  - The C extension means platform-specific builds — verify Docker base image compatibility.

## Known Gotchas / Edge Cases

### 1. License Change (AGPL-3.0) — Most Critical Issue
Starting around v1.24.x, PyMuPDF adopted AGPL-3.0 dual licensing. For a web application serving users (like this FastAPI-based career intelligence assistant), AGPL-3.0 requires:
- Making the complete source code of the application available to all network users
- All modifications must also be AGPL-3.0 licensed

**Action required**: Legal review of AGPL implications for this project, or purchase commercial license, or evaluate alternatives.

### 2. Import Name Change
```python
# Old (pre-1.24.0):
import fitz

# New (1.24.0+):
import pymupdf  # 'fitz' still works as alias but is deprecated
```
When upgrading, update all imports. The `fitz` alias may be removed in a future version.

### 3. Malicious PDF Handling
PDF is a complex format and a common attack vector. Defensive measures for user-uploaded resumes:
```python
import pymupdf

MAX_PDF_SIZE = 10 * 1024 * 1024  # 10MB limit for resumes
MAX_PAGES = 50  # Resumes shouldn't exceed this
EXTRACTION_TIMEOUT = 30  # seconds

def safe_extract_text(file_bytes: bytes) -> str:
    if len(file_bytes) > MAX_PDF_SIZE:
        raise ValueError("PDF exceeds maximum allowed size")

    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
    try:
        if doc.page_count > MAX_PAGES:
            raise ValueError("PDF has too many pages")

        text = ""
        for page in doc:
            text += page.get_text("text")
        return text
    finally:
        doc.close()
```

Additional protections to consider:
- Disable JavaScript execution in PDFs (PyMuPDF does not execute JS, but verify)
- Strip embedded files/attachments before processing
- Validate with `python-magic`/`puremagic` that the file is actually a PDF before opening

### 4. Memory Usage on Large Files
- PyMuPDF loads pages lazily but the document object holds the file open.
- For very large PDFs (100+ pages, image-heavy), memory usage can spike to hundreds of MB.
- Always use `doc.close()` or context managers to release resources promptly.
- For batch processing, extract one document at a time rather than opening many simultaneously.
- Consider `page.get_text()` per page with intermediate cleanup for very large documents.

### 5. Text Extraction Quality
- **Excellent** for text-based PDFs (the common case for resumes).
- **Poor** for scanned/image-based PDFs — returns empty strings. No built-in OCR.
  - If OCR is needed, PyMuPDF supports Tesseract integration via `page.get_text("text", textpage=None, flags=pymupdf.TEXT_PRESERVE_WHITESPACE)` with Tesseract installed, or use the `pymupdf` + `pytesseract` combo.
- **Multi-column layouts**: `get_text("text")` may interleave columns. Use `get_text("blocks")` or `get_text("dict")` for layout-aware extraction if resumes have complex formatting.
- **Headers/footers**: Repeated on every page. May want to deduplicate for clean text.
- **Ligatures and special characters**: Generally handled well, but some PDFs with unusual fonts may produce garbled text. Test with diverse resume samples.

### 6. Breaking Changes Since 1.23.22

**1.23.22 to 1.27.2 (current):**

- **v1.24.0 (major)**: Import name changed from `fitz` to `pymupdf`. The `fitz` name still works as an alias but is deprecated.
- **v1.24.0**: New `pymupdf4llm` companion package for LLM-optimized text extraction (Markdown output). Worth evaluating for this project's RAG pipeline.
- **v1.24.x**: License changed to AGPL-3.0 / Commercial dual license.
- **v1.25.0**: Some deprecated methods removed. `Page.getText()` (camelCase) fully removed — use `page.get_text()`.
- **v1.25.x+**: Improved text extraction for complex layouts. Better Unicode handling.
- **v1.26.0+**: Performance improvements for large documents. New story/content extraction APIs.
- **v1.27.x**: Continued refinements. Check changelog for specific deprecation removals.

### 7. `pymupdf4llm` — Worth Evaluating
Since v1.24.0, the `pymupdf4llm` package provides Markdown-formatted extraction optimized for LLM consumption:
```python
import pymupdf4llm

md_text = pymupdf4llm.to_markdown("resume.pdf")
```
This may produce better input for the RAG pipeline than plain text extraction, as it preserves structural information (headings, lists, bold/italic) that helps LLMs understand document structure.

### 8. Docker / CI Considerations
- PyMuPDF ships pre-built wheels for `manylinux`, macOS (x86_64 + arm64), and Windows.
- If building from source is needed (rare architectures), requires `mupdf` C library headers.
- Wheel size is ~15-20MB due to bundled MuPDF.
- No system dependencies required when using wheels.

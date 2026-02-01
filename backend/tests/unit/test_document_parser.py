"""
Unit tests for Document Parser Service.

TDD: These tests are written BEFORE implementation.
Tests should FAIL until document_parser.py is implemented.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestDocumentParser:
    """Test suite for document parsing functionality."""

    # ========================================================================
    # PDF Parsing Tests
    # ========================================================================

    def test_parse_pdf_extracts_text(self, tmp_path: Path):
        """PDF parser should extract text content from valid PDF files."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()

        # Create a file with PDF magic bytes
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 test")

        # Mock PyMuPDF to return text
        mock_page = MagicMock()
        mock_page.get_text.return_value = "Sample resume content"

        mock_doc = MagicMock()
        mock_doc.__iter__ = lambda self: iter([mock_page])

        with patch("fitz.open", return_value=mock_doc):
            result = parser.parse(pdf_path)

        assert result is not None
        assert isinstance(result, str)
        assert "Sample resume content" in result

    def test_parse_pdf_handles_empty_file(self, tmp_path: Path):
        """PDF parser should raise error for empty files."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        pdf_path = tmp_path / "empty.pdf"
        pdf_path.write_bytes(b"")

        with pytest.raises(ValueError):
            parser.parse(pdf_path)

    def test_parse_pdf_handles_corrupted_file(self, tmp_path: Path):
        """PDF parser should raise error for corrupted PDF files."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        pdf_path = tmp_path / "corrupted.pdf"
        pdf_path.write_bytes(b"%PDF-1.4 corrupted")

        # Mock PyMuPDF to raise an exception
        with patch("fitz.open", side_effect=Exception("Invalid PDF")):
            with pytest.raises(ValueError):
                parser.parse(pdf_path)

    # ========================================================================
    # DOCX Parsing Tests
    # ========================================================================

    def test_parse_docx_extracts_text(self, tmp_path: Path):
        """DOCX parser should extract text content from valid DOCX files."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()

        # Mock python-docx
        mock_para = MagicMock()
        mock_para.text = "Sample DOCX content"

        mock_doc = MagicMock()
        mock_doc.paragraphs = [mock_para]
        mock_doc.tables = []

        with patch("docx.Document", return_value=mock_doc):
            result = parser.parse_docx_content(b"PK\x03\x04mock")

        assert result is not None
        assert isinstance(result, str)
        assert "Sample DOCX content" in result

    def test_parse_docx_handles_empty_file(self):
        """DOCX parser should raise error for empty files."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()

        with pytest.raises(ValueError, match="empty"):
            parser.parse_docx_content(b"")

    # ========================================================================
    # Plain Text Parsing Tests
    # ========================================================================

    def test_parse_text_returns_content(self):
        """Text parser should return the plain text content."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        text = "This is a resume content"

        result = parser.parse_text(text)

        assert result == text

    def test_parse_text_strips_whitespace(self):
        """Text parser should strip leading/trailing whitespace."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        text = "   Resume content   \n\n"

        result = parser.parse_text(text)

        assert result == "Resume content"

    def test_parse_text_handles_empty_string(self):
        """Text parser should raise error for empty strings."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()

        with pytest.raises(ValueError, match="empty"):
            parser.parse_text("")

    def test_parse_text_handles_whitespace_only(self):
        """Text parser should raise error for whitespace-only strings."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()

        with pytest.raises(ValueError, match="empty"):
            parser.parse_text("   \n\t  ")

    # ========================================================================
    # File Type Detection Tests
    # ========================================================================

    def test_detect_file_type_pdf(self, tmp_path: Path):
        """Should correctly detect PDF file type."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"%PDF-1.4")

        file_type = parser.detect_file_type(pdf_path)

        assert file_type == "pdf"

    def test_detect_file_type_docx(self, tmp_path: Path):
        """Should correctly detect DOCX file type."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        # DOCX magic bytes (PK zip header)
        docx_path = tmp_path / "test.docx"
        docx_path.write_bytes(b"PK\x03\x04")

        file_type = parser.detect_file_type(docx_path)

        assert file_type == "docx"

    def test_detect_file_type_txt(self, tmp_path: Path):
        """Should correctly detect plain text file type."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        txt_path = tmp_path / "test.txt"
        txt_path.write_text("Plain text content")

        file_type = parser.detect_file_type(txt_path)

        assert file_type == "txt"

    def test_reject_unsupported_file_type(self, tmp_path: Path):
        """Should reject unsupported file types."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        exe_path = tmp_path / "malware.exe"
        exe_path.write_bytes(b"MZ\x90\x00")  # PE executable header

        with pytest.raises(ValueError, match="[Uu]nsupported"):
            parser.detect_file_type(exe_path)

    # ========================================================================
    # File Size Validation Tests
    # ========================================================================

    def test_reject_file_over_max_size(self, tmp_path: Path):
        """Should reject files exceeding maximum size limit (10MB)."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        large_file = tmp_path / "large.pdf"
        # Create file larger than 10MB
        large_file.write_bytes(b"x" * (11 * 1024 * 1024))

        with pytest.raises(ValueError, match="[Ss]ize"):
            parser.validate_file_size(large_file)

    def test_accept_file_under_max_size(self, tmp_path: Path):
        """Should accept files under maximum size limit."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        small_file = tmp_path / "small.pdf"
        small_file.write_bytes(b"x" * 1024)  # 1KB

        # Should not raise
        parser.validate_file_size(small_file)

    # ========================================================================
    # Content Length Validation Tests
    # ========================================================================

    def test_reject_content_over_max_length(self):
        """Should reject content exceeding maximum character limit (50K)."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        long_content = "x" * 60000  # 60K characters

        with pytest.raises(ValueError, match="[Ll]ength"):
            parser.validate_content_length(long_content)

    def test_accept_content_under_max_length(self):
        """Should accept content under maximum character limit."""
        from app.services.document_parser import DocumentParser

        parser = DocumentParser()
        short_content = "x" * 1000

        # Should not raise
        parser.validate_content_length(short_content)

    # ========================================================================
    # get_document_parser Tests
    # ========================================================================

    def test_get_document_parser_returns_instance(self):
        """Should return a DocumentParser instance."""
        from app.services.document_parser import get_document_parser

        parser = get_document_parser()

        assert parser is not None
        from app.services.document_parser import DocumentParser
        assert isinstance(parser, DocumentParser)

    def test_get_document_parser_returns_singleton(self):
        """Should return the same instance on multiple calls."""
        from app.services.document_parser import get_document_parser

        parser1 = get_document_parser()
        parser2 = get_document_parser()

        assert parser1 is parser2

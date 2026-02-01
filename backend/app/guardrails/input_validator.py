"""
Input Validator.

Validates file types, sizes, and content limits for secure document processing.
"""

import logging
import os
from pathlib import Path
from typing import Tuple, Union

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Validates input files and content for security and size constraints.

    Features:
    - File type validation using magic bytes and extensions
    - File size limits (max 10MB)
    - Content length limits (max 50K characters)
    - Rejection of potentially dangerous file types
    """

    # Magic bytes for file type detection
    MAGIC_BYTES = {
        "pdf": b"%PDF",
        "docx": b"PK\x03\x04",  # DOCX is a ZIP file
        "zip": b"PK\x03\x04",
    }

    # Allowed file extensions (lowercase)
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".txt", ".text"}

    # Dangerous file extensions to block
    BLOCKED_EXTENSIONS = {
        ".exe", ".dll", ".bat", ".cmd", ".ps1", ".sh", ".bash",
        ".js", ".vbs", ".wsf", ".msi", ".scr", ".com", ".pif",
        ".py", ".rb", ".pl", ".php", ".jar", ".class",
    }

    # Maximum file size in bytes (10 MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024

    # Maximum content length in characters (50K)
    MAX_CONTENT_LENGTH = 50000

    def __init__(
        self,
        max_file_size: int = None,
        max_content_length: int = None,
    ):
        """
        Initialize the input validator.

        Args:
            max_file_size: Maximum file size in bytes (default 10MB)
            max_content_length: Maximum content length in chars (default 50K)
        """
        self.max_file_size = max_file_size or self.MAX_FILE_SIZE
        self.max_content_length = max_content_length or self.MAX_CONTENT_LENGTH

    def validate_file(self, file_path: Union[str, Path]) -> Tuple[bool, str]:
        """
        Validate a file for type and size.

        Args:
            file_path: Path to the file to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file passes all checks
            - error_message: Empty string if valid, otherwise description of issue
        """
        file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            return False, "File does not exist"

        if not file_path.is_file():
            return False, "Path is not a file"

        # Check file extension
        extension = file_path.suffix.lower()

        # Block dangerous extensions
        if extension in self.BLOCKED_EXTENSIONS:
            logger.warning(f"Blocked file with dangerous extension: {extension}")
            return False, f"Unsupported file type: {extension} files are not allowed"

        # Check file size
        file_size = file_path.stat().st_size
        if file_size > self.max_file_size:
            size_mb = file_size / (1024 * 1024)
            max_mb = self.max_file_size / (1024 * 1024)
            logger.warning(f"File too large: {size_mb:.2f}MB > {max_mb:.2f}MB")
            return False, f"File size ({size_mb:.1f}MB) exceeds maximum allowed size ({max_mb:.0f}MB)"

        # Check if file is empty
        if file_size == 0:
            return False, "File is empty"

        # Validate file type by magic bytes and extension
        is_valid_type, type_error = self._validate_file_type(file_path, extension)
        if not is_valid_type:
            return False, type_error

        return True, ""

    def _validate_file_type(self, file_path: Path, extension: str) -> Tuple[bool, str]:
        """
        Validate file type using magic bytes and extension.

        Args:
            file_path: Path to the file
            extension: File extension (lowercase)

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            with open(file_path, "rb") as f:
                # Read first 16 bytes for magic number detection
                header = f.read(16)
        except Exception as e:
            logger.error(f"Error reading file header: {e}")
            return False, "Unable to read file"

        # Check for blocked file types by magic bytes
        if self._is_executable(header):
            return False, "Unsupported file type: executable files are not allowed"

        # Validate based on extension
        if extension == ".pdf":
            if not header.startswith(self.MAGIC_BYTES["pdf"]):
                return False, "File content does not match PDF format"
            return True, ""

        elif extension in {".docx", ".doc"}:
            # DOCX files are ZIP archives
            if header.startswith(self.MAGIC_BYTES["docx"]):
                return True, ""
            # Old .doc format has different magic bytes
            if header.startswith(b"\xd0\xcf\x11\xe0"):  # OLE compound document
                return True, ""
            return False, "File content does not match Word document format"

        elif extension in {".txt", ".text"}:
            # Text files should be readable as text
            # Check that it doesn't start with binary signatures
            if self._looks_like_binary(header):
                return False, "File appears to be binary, not text"
            return True, ""

        elif extension in self.ALLOWED_EXTENSIONS:
            # Other allowed extensions
            return True, ""

        else:
            # Unknown extension
            return False, f"Unsupported file type: {extension}"

    def _is_executable(self, header: bytes) -> bool:
        """Check if file header indicates an executable."""
        # Windows PE executable
        if header.startswith(b"MZ"):
            return True
        # ELF executable (Linux)
        if header.startswith(b"\x7fELF"):
            return True
        # Mach-O executable (macOS)
        if header[:4] in (b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe"):
            return True
        # Shell script
        if header.startswith(b"#!"):
            return True
        return False

    def _looks_like_binary(self, header: bytes) -> bool:
        """Check if content appears to be binary rather than text."""
        # Check for common binary file signatures
        binary_signatures = [
            b"MZ",  # Windows executable
            b"\x7fELF",  # ELF
            b"\xfe\xed\xfa",  # Mach-O
            b"\xca\xfe\xba\xbe",  # Mach-O universal
            b"\x89PNG",  # PNG
            b"\xff\xd8\xff",  # JPEG
            b"GIF8",  # GIF
            b"RIFF",  # AVI, WAV
        ]

        for sig in binary_signatures:
            if header.startswith(sig):
                return True

        # Check for high ratio of non-printable characters
        if header:
            non_printable = sum(1 for b in header if b < 32 and b not in (9, 10, 13))
            if non_printable / len(header) > 0.3:
                return True

        return False

    def validate_content(self, content: str) -> Tuple[bool, str]:
        """
        Validate text content for length and basic safety.

        Args:
            content: Text content to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if content is None:
            return False, "Content is None"

        # Check content length
        if len(content) > self.max_content_length:
            logger.warning(
                f"Content too long: {len(content)} > {self.max_content_length} chars"
            )
            return False, (
                f"Content length ({len(content)} chars) exceeds maximum "
                f"allowed length ({self.max_content_length} chars)"
            )

        return True, ""

    def validate_file_count(self, count: int, max_count: int = 5) -> Tuple[bool, str]:
        """
        Validate that number of files doesn't exceed limit.

        Args:
            count: Number of files
            max_count: Maximum allowed files (default 5)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if count > max_count:
            return False, f"Too many files: {count} exceeds maximum of {max_count}"
        return True, ""


# Default validator instance
_default_validator = None


def get_input_validator() -> InputValidator:
    """
    Get the default input validator instance.

    Returns:
        InputValidator instance
    """
    global _default_validator
    if _default_validator is None:
        _default_validator = InputValidator()
    return _default_validator

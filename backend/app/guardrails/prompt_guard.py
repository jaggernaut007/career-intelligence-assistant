"""
Prompt Injection Guard.

Detects and prevents prompt injection attacks in user input.
"""

import logging
import re
import unicodedata
from typing import List, Tuple

logger = logging.getLogger(__name__)


class PromptGuard:
    """
    Guards against prompt injection attacks.

    Detects patterns like:
    - "Ignore previous instructions"
    - "New instructions:"
    - System prompt leak attempts
    - Role switching attempts
    - Control character injection
    - Unicode homoglyph attacks
    """

    # Injection patterns to detect
    INJECTION_PATTERNS = [
        # Ignore/override instructions
        (r'ignore\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?', 'ignore_instructions'),
        (r'disregard\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?', 'disregard_instructions'),
        (r'forget\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?', 'forget_instructions'),
        (r'override\s+(all\s+)?(previous|prior|above|earlier)\s+instructions?', 'override_instructions'),

        # New instruction injection
        (r'new\s+instructions?\s*:', 'new_instructions'),
        (r'updated\s+instructions?\s*:', 'updated_instructions'),
        (r'real\s+instructions?\s*:', 'real_instructions'),
        (r'actual\s+instructions?\s*:', 'actual_instructions'),

        # System prompt leak attempts
        (r'(what|show|print|reveal|display|tell)\s+(are\s+)?(your|the)\s+system\s+(prompt|instructions?)', 'system_prompt_leak'),
        (r'(what|show|print|reveal|display|tell)\s+(me\s+)?(your|the)\s+(initial|original)\s+(prompt|instructions?)', 'initial_prompt_leak'),
        (r'repeat\s+(your\s+)?system\s+(prompt|instructions?)', 'repeat_system_prompt'),
        (r'output\s+(your\s+)?system\s+(prompt|instructions?)', 'output_system_prompt'),

        # Role switching attempts
        (r'<\|system\|>', 'role_tag_system'),
        (r'<\|assistant\|>', 'role_tag_assistant'),
        (r'<\|user\|>', 'role_tag_user'),
        (r'\[INST\]', 'inst_tag'),
        (r'\[/INST\]', 'inst_close_tag'),
        (r'<<SYS>>', 'llama_sys_tag'),
        (r'<</SYS>>', 'llama_sys_close_tag'),

        # Direct manipulation attempts
        (r'you\s+are\s+now\s+a', 'role_change'),
        (r'act\s+as\s+(if\s+you\s+are|a)', 'act_as'),
        (r'pretend\s+(to\s+be|you\s+are)', 'pretend'),
        (r'roleplay\s+as', 'roleplay'),

        # Jailbreak attempts
        (r'do\s+anything\s+now', 'dan_jailbreak'),
        (r'developer\s+mode', 'developer_mode'),
        (r'jailbreak', 'jailbreak_keyword'),
    ]

    def __init__(self):
        """Initialize the prompt guard."""
        self._compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), name)
            for pattern, name in self.INJECTION_PATTERNS
        ]

    def validate(self, text: str) -> Tuple[bool, str]:
        """
        Validate input text for prompt injection attempts.

        Args:
            text: Text to validate

        Returns:
            Tuple of (is_safe, reason)
            - is_safe: True if text is safe, False if injection detected
            - reason: Empty string if safe, otherwise description of detected issue
        """
        if not text:
            return True, ""

        text_normalized = self._normalize_text(text)

        # Check each injection pattern
        for pattern, pattern_name in self._compiled_patterns:
            if pattern.search(text_normalized):
                logger.warning(f"Prompt injection detected: {pattern_name}")
                return False, f"Potential prompt injection detected ({pattern_name})"

        # Check for suspicious character sequences
        if self._has_suspicious_characters(text):
            return False, "Suspicious character sequences detected"

        return True, ""

    def sanitize(self, text: str) -> str:
        """
        Sanitize input text by removing potentially harmful content.

        Args:
            text: Text to sanitize

        Returns:
            Sanitized text
        """
        if not text:
            return text

        # Remove control characters (except newlines and tabs)
        sanitized = ''.join(
            char for char in text
            if char in '\n\t\r' or (ord(char) >= 32 and ord(char) != 127)
        )

        # Normalize unicode to NFC form
        sanitized = unicodedata.normalize('NFC', sanitized)

        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')

        # Remove other problematic control characters
        for i in range(32):
            if i not in (9, 10, 13):  # Keep tab, newline, carriage return
                sanitized = sanitized.replace(chr(i), '')

        return sanitized

    def _normalize_text(self, text: str) -> str:
        """Normalize text for pattern matching."""
        # Normalize unicode
        normalized = unicodedata.normalize('NFKC', text)

        # Convert to lowercase for pattern matching
        normalized = normalized.lower()

        # Collapse multiple whitespace
        normalized = re.sub(r'\s+', ' ', normalized)

        return normalized

    def _has_suspicious_characters(self, text: str) -> bool:
        """Check for suspicious character sequences."""
        # Check for excessive special characters
        special_char_ratio = sum(1 for c in text if not c.isalnum() and not c.isspace()) / max(len(text), 1)
        if special_char_ratio > 0.5:
            return True

        # Check for non-ASCII characters in suspicious positions
        # (This is a simple heuristic that might need tuning)
        suspicious_unicode_categories = {'Cf', 'Co', 'Cn'}  # Format, Private Use, Unassigned
        for char in text:
            if unicodedata.category(char) in suspicious_unicode_categories:
                return True

        return False

    def wrap_user_input(self, user_input: str) -> str:
        """
        Wrap user input in delimiter tags for safer prompt construction.

        Args:
            user_input: Raw user input

        Returns:
            Wrapped user input with delimiters
        """
        sanitized = self.sanitize(user_input)
        return f"<user_input>\n{sanitized}\n</user_input>"

    def is_safe(self, text: str) -> bool:
        """
        Quick check if text is safe.

        Args:
            text: Text to check

        Returns:
            True if safe, False if potentially dangerous
        """
        is_safe, _ = self.validate(text)
        return is_safe


# Default prompt guard instance
_default_guard = None


def get_prompt_guard() -> PromptGuard:
    """
    Get the default prompt guard instance.

    Returns:
        PromptGuard instance
    """
    global _default_guard
    if _default_guard is None:
        _default_guard = PromptGuard()
    return _default_guard

"""
Output Filter.

Filters LLM outputs to remove leaked system prompts, validate JSON,
and redact any hallucinated PII.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class OutputFilter:
    """
    Filters and validates LLM output for security and compliance.

    Features:
    - Removes leaked system prompt content
    - Validates JSON structure against expected schema
    - Redacts hallucinated PII from output
    - Sanitizes output for safe display
    """

    # Patterns that indicate leaked system prompts
    SYSTEM_PROMPT_PATTERNS = [
        r'\[SYSTEM\]:?\s*.*',
        r'<\|system\|>.*?<\|/system\|>',
        r'<<SYS>>.*?<</SYS>>',
        r'\[INST\].*?\[/INST\]',
        r'System:\s*You are an? (AI|assistant|helpful)',
        r'You are an? AI assistant',
        r'As an AI language model',
        r'I am an AI assistant',
        r'My instructions (are|say|tell)',
        r'My system prompt',
        r'I was instructed to',
        r'According to my instructions',
        r'My programming (says|tells|instructs)',
    ]

    # PII patterns for output filtering
    PII_PATTERNS = [
        # Email
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 'EMAIL'),
        # Phone numbers
        (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', 'PHONE'),
        (r'\(\d{3}\)\s*\d{3}[-.]?\d{4}', 'PHONE'),
        # SSN
        (r'\b\d{3}-\d{2}-\d{4}\b', 'SSN'),
    ]

    def __init__(self, redact_pii: bool = True):
        """
        Initialize the output filter.

        Args:
            redact_pii: Whether to redact PII patterns in output
        """
        self.redact_pii = redact_pii
        self._compiled_system_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.SYSTEM_PROMPT_PATTERNS
        ]
        self._compiled_pii_patterns = [
            (re.compile(pattern), pii_type)
            for pattern, pii_type in self.PII_PATTERNS
        ]

    def filter(self, output: str) -> str:
        """
        Filter LLM output for security.

        Removes:
        - Leaked system prompts
        - Hallucinated PII (if redact_pii is True)

        Args:
            output: Raw LLM output

        Returns:
            Filtered output safe for display
        """
        if not output:
            return output

        filtered = output

        # Remove leaked system prompts
        filtered = self._remove_system_prompt_leaks(filtered)

        # Redact any PII in output
        if self.redact_pii:
            filtered = self._redact_output_pii(filtered)

        # Remove any remaining suspicious patterns
        filtered = self._sanitize_output(filtered)

        return filtered

    def _remove_system_prompt_leaks(self, text: str) -> str:
        """Remove any leaked system prompt content."""
        result = text

        for pattern in self._compiled_system_patterns:
            result = pattern.sub('', result)

        # Clean up any resulting double spaces or empty lines
        result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
        result = re.sub(r'  +', ' ', result)

        return result.strip()

    def _redact_output_pii(self, text: str) -> str:
        """Redact PII patterns from output."""
        result = text

        for pattern, pii_type in self._compiled_pii_patterns:
            result = pattern.sub(f'[REDACTED-{pii_type}]', result)

        return result

    def _sanitize_output(self, text: str) -> str:
        """Additional sanitization for safe display."""
        # Remove control characters
        sanitized = ''.join(
            char for char in text
            if char in '\n\t\r' or (ord(char) >= 32 and ord(char) != 127)
        )

        # Remove null bytes
        sanitized = sanitized.replace('\x00', '')

        return sanitized

    def validate_json(
        self,
        json_str: str,
        expected_keys: Optional[List[str]] = None,
        schema: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str]:
        """
        Validate JSON output structure.

        Args:
            json_str: JSON string to validate
            expected_keys: Optional list of keys that must be present
            schema: Optional schema dict for validation

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Try to parse JSON
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON: {e}")
            return False, f"Invalid JSON: {str(e)}"

        # Check expected keys if provided
        if expected_keys:
            if not isinstance(data, dict):
                return False, "JSON must be an object when expected_keys is specified"

            missing_keys = set(expected_keys) - set(data.keys())
            if missing_keys:
                return False, f"Missing required keys: {', '.join(missing_keys)}"

        # Validate against schema if provided
        if schema:
            is_valid, error = self._validate_against_schema(data, schema)
            if not is_valid:
                return False, error

        return True, ""

    def _validate_against_schema(
        self,
        data: Any,
        schema: Dict[str, Any],
        path: str = "root"
    ) -> Tuple[bool, str]:
        """
        Basic schema validation.

        Args:
            data: Data to validate
            schema: Schema definition
            path: Current path for error messages

        Returns:
            Tuple of (is_valid, error_message)
        """
        expected_type = schema.get("type")

        if expected_type == "object":
            if not isinstance(data, dict):
                return False, f"{path}: expected object, got {type(data).__name__}"

            # Check required properties
            required = schema.get("required", [])
            for key in required:
                if key not in data:
                    return False, f"{path}: missing required property '{key}'"

            # Validate properties
            properties = schema.get("properties", {})
            for key, prop_schema in properties.items():
                if key in data:
                    is_valid, error = self._validate_against_schema(
                        data[key], prop_schema, f"{path}.{key}"
                    )
                    if not is_valid:
                        return False, error

        elif expected_type == "array":
            if not isinstance(data, list):
                return False, f"{path}: expected array, got {type(data).__name__}"

            # Validate items
            items_schema = schema.get("items")
            if items_schema:
                for i, item in enumerate(data):
                    is_valid, error = self._validate_against_schema(
                        item, items_schema, f"{path}[{i}]"
                    )
                    if not is_valid:
                        return False, error

        elif expected_type == "string":
            if not isinstance(data, str):
                return False, f"{path}: expected string, got {type(data).__name__}"

        elif expected_type == "number":
            if not isinstance(data, (int, float)):
                return False, f"{path}: expected number, got {type(data).__name__}"

        elif expected_type == "integer":
            if not isinstance(data, int) or isinstance(data, bool):
                return False, f"{path}: expected integer, got {type(data).__name__}"

        elif expected_type == "boolean":
            if not isinstance(data, bool):
                return False, f"{path}: expected boolean, got {type(data).__name__}"

        return True, ""

    def filter_json_output(
        self,
        json_str: str,
        expected_keys: Optional[List[str]] = None,
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """
        Parse, validate, and filter JSON output.

        Args:
            json_str: JSON string to process
            expected_keys: Optional list of required keys

        Returns:
            Tuple of (parsed_data, error_message)
            - parsed_data: Parsed and filtered dict, or None if invalid
            - error_message: Empty string if valid, otherwise error description
        """
        # First validate the JSON
        is_valid, error = self.validate_json(json_str, expected_keys)
        if not is_valid:
            return None, error

        # Parse and process
        try:
            data = json.loads(json_str)

            # Recursively filter string values
            filtered_data = self._filter_dict_values(data)

            return filtered_data, ""

        except Exception as e:
            logger.error(f"Error processing JSON: {e}")
            return None, f"Error processing JSON: {str(e)}"

    def _filter_dict_values(self, obj: Any) -> Any:
        """Recursively filter string values in a dict/list structure."""
        if isinstance(obj, dict):
            return {k: self._filter_dict_values(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._filter_dict_values(item) for item in obj]
        elif isinstance(obj, str):
            return self.filter(obj)
        else:
            return obj


# Default filter instance
_default_filter = None


def get_output_filter(redact_pii: bool = True) -> OutputFilter:
    """
    Get the default output filter instance.

    Args:
        redact_pii: Whether to redact PII in output

    Returns:
        OutputFilter instance
    """
    global _default_filter
    if _default_filter is None:
        _default_filter = OutputFilter(redact_pii=redact_pii)
    return _default_filter

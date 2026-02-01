"""
PII Detector using Microsoft Presidio.

Detects and redacts Personally Identifiable Information from text.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PIIDetector:
    """
    Detects and redacts PII from text using pattern matching and Presidio.

    Supports detection of:
    - SSN (Social Security Numbers)
    - Phone numbers (various formats)
    - Email addresses
    - Street addresses
    - Credit card numbers
    """

    def __init__(self):
        """Initialize PII detector with Presidio analyzer."""
        self._analyzer = None
        self._anonymizer = None
        self._initialized = False
        self._initialize()

    def _initialize(self) -> None:
        """Lazy initialize Presidio components."""
        if self._initialized:
            return

        try:
            from presidio_analyzer import AnalyzerEngine
            from presidio_analyzer.nlp_engine import NlpEngineProvider
            from presidio_anonymizer import AnonymizerEngine

            # Configure to use the smaller spacy model for better compatibility
            config = {
                'nlp_engine_name': 'spacy',
                'models': [{'lang_code': 'en', 'model_name': 'en_core_web_sm'}]
            }
            provider = NlpEngineProvider(nlp_configuration=config)
            nlp_engine = provider.create_engine()

            self._analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
            self._anonymizer = AnonymizerEngine()
            self._initialized = True
            logger.info("Presidio PII detector initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize Presidio: {e}. Using fallback patterns.")
            self._initialized = True  # Mark as initialized to avoid retrying

    def detect(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect PII in text.

        Args:
            text: Text to analyze for PII

        Returns:
            List of detected PII items with type, value, and position
        """
        if not text or not text.strip():
            return []

        results = []

        # Try Presidio first
        if self._analyzer:
            try:
                analyzer_results = self._analyzer.analyze(
                    text=text,
                    language="en",
                    entities=[
                        "PERSON",
                        "EMAIL_ADDRESS",
                        "PHONE_NUMBER",
                        "US_SSN",
                        "CREDIT_CARD",
                        "LOCATION",
                        "US_DRIVER_LICENSE",
                        "US_PASSPORT",
                        "US_BANK_NUMBER",
                    ],
                )

                for result in analyzer_results:
                    pii_type = self._map_presidio_type(result.entity_type)
                    results.append({
                        "type": pii_type,
                        "value": text[result.start:result.end],
                        "start": result.start,
                        "end": result.end,
                        "score": result.score,
                    })
            except Exception as e:
                logger.warning(f"Presidio analysis failed: {e}. Using fallback.")

        # Always run fallback patterns for common PII
        fallback_results = self._detect_with_patterns(text)

        # Merge results, avoiding duplicates
        seen_ranges = set((r["start"], r["end"]) for r in results)
        for fb_result in fallback_results:
            if (fb_result["start"], fb_result["end"]) not in seen_ranges:
                results.append(fb_result)

        return results

    def _map_presidio_type(self, presidio_type: str) -> str:
        """Map Presidio entity types to our standard types."""
        type_mapping = {
            "US_SSN": "SSN",
            "PHONE_NUMBER": "PHONE_NUMBER",
            "EMAIL_ADDRESS": "EMAIL_ADDRESS",
            "PERSON": "PERSON",
            "CREDIT_CARD": "CREDIT_CARD",
            "LOCATION": "ADDRESS",
            "US_DRIVER_LICENSE": "DRIVER_LICENSE",
            "US_PASSPORT": "PASSPORT",
            "US_BANK_NUMBER": "BANK_NUMBER",
        }
        return type_mapping.get(presidio_type, presidio_type)

    def _detect_with_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Fallback pattern-based PII detection."""
        results = []

        # SSN patterns
        ssn_patterns = [
            (r'\b\d{3}-\d{2}-\d{4}\b', "SSN"),  # XXX-XX-XXXX
            (r'\b\d{9}\b', "SSN"),  # 9 consecutive digits (could be SSN)
        ]

        # Phone patterns
        phone_patterns = [
            (r'\(\d{3}\)\s*\d{3}-\d{4}', "PHONE_NUMBER"),  # (XXX) XXX-XXXX
            (r'\b\d{3}-\d{3}-\d{4}\b', "PHONE_NUMBER"),  # XXX-XXX-XXXX
            (r'\b\d{3}\.\d{3}\.\d{4}\b', "PHONE_NUMBER"),  # XXX.XXX.XXXX
            (r'\b\d{10}\b', "PHONE_NUMBER"),  # 10 consecutive digits
        ]

        # Email pattern
        email_pattern = (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "EMAIL_ADDRESS")

        # Address patterns (US-style)
        address_patterns = [
            # Street address with number: "123 Main Street", "456 Oak Ave"
            (r'\b\d{1,5}\s+[A-Za-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Court|Ct|Way|Place|Pl|Circle|Cir)\b', "ADDRESS"),
            # ZIP code patterns
            (r'\b\d{5}(-\d{4})?\b', "ADDRESS"),
        ]

        # Combine all patterns
        all_patterns = ssn_patterns + phone_patterns + [email_pattern] + address_patterns

        for pattern, pii_type in all_patterns:
            for match in re.finditer(pattern, text):
                results.append({
                    "type": pii_type,
                    "value": match.group(),
                    "start": match.start(),
                    "end": match.end(),
                    "score": 0.85,  # Pattern match confidence
                })

        return results

    def redact(self, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Redact all PII from text.

        Args:
            text: Text to redact PII from
            replacement: String to replace PII with

        Returns:
            Text with PII redacted
        """
        if not text or not text.strip():
            return text

        # Try Presidio anonymizer first
        if self._analyzer and self._anonymizer:
            try:
                from presidio_anonymizer.entities import OperatorConfig

                analyzer_results = self._analyzer.analyze(
                    text=text,
                    language="en",
                    entities=[
                        "PERSON",
                        "EMAIL_ADDRESS",
                        "PHONE_NUMBER",
                        "US_SSN",
                        "CREDIT_CARD",
                        "LOCATION",
                    ],
                )

                if analyzer_results:
                    anonymized = self._anonymizer.anonymize(
                        text=text,
                        analyzer_results=analyzer_results,
                        operators={
                            "DEFAULT": OperatorConfig("replace", {"new_value": replacement})
                        }
                    )
                    text = anonymized.text
            except Exception as e:
                logger.warning(f"Presidio anonymization failed: {e}. Using fallback.")

        # Always apply pattern-based redaction as backup
        text = self._redact_with_patterns(text, replacement)

        return text

    def _redact_with_patterns(self, text: str, replacement: str) -> str:
        """Fallback pattern-based redaction."""
        # SSN patterns
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', replacement, text)

        # Phone patterns
        text = re.sub(r'\(\d{3}\)\s*\d{3}-\d{4}', replacement, text)
        text = re.sub(r'\b\d{3}-\d{3}-\d{4}\b', replacement, text)

        # Email pattern
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', replacement, text)

        return text

    def has_pii(self, text: str) -> bool:
        """Check if text contains any PII."""
        return len(self.detect(text)) > 0


# Default detector instance
_default_detector = None


def get_pii_detector() -> PIIDetector:
    """
    Get the default PII detector instance.

    Returns:
        PIIDetector instance
    """
    global _default_detector
    if _default_detector is None:
        _default_detector = PIIDetector()
    return _default_detector

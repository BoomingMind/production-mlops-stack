"""
Output Guards Module

Provides output moderation for LLM responses before returning to users.

Rule Types Implemented:
    1. Toxicity Filter - Detects harmful/toxic content in responses
    2. Hallucination Filter - Detects claims not grounded in context
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum


class OutputViolationType(Enum):
    """Types of output violations."""

    TOXICITY_PROFANITY = "toxicity_profanity"
    TOXICITY_HARMFUL = "toxicity_harmful"
    TOXICITY_HATE = "toxicity_hate"
    HALLUCINATION_UNSUPPORTED = "hallucination_unsupported"
    HALLUCINATION_FABRICATED_SOURCE = "hallucination_fabricated_source"
    HALLUCINATION_LOW_CONFIDENCE = "hallucination_low_confidence"
    FORMAT_INVALID = "format_invalid"


@dataclass
class OutputValidationResult:
    """Result of output validation."""

    passed: bool
    violations: List[OutputViolationType] = field(default_factory=list)
    violation_details: List[str] = field(default_factory=list)
    confidence_score: float = 1.0
    filtered_response: Optional[str] = None
    original_response: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for logging."""
        return {
            "passed": self.passed,
            "violations": [v.value for v in self.violations],
            "violation_details": self.violation_details,
            "confidence_score": self.confidence_score,
            "has_filtered": self.filtered_response is not None,
        }


class OutputGuard:
    """
    Output moderation guard for LLM responses.

    Implements two rule types:
    1. Toxicity Filter - Blocks harmful content
    2. Hallucination Filter - Validates claims against context

    Usage:
        guard = OutputGuard()
        result = guard.validate(response_text, context_chunks)
        if result.passed:
            # Return response
        else:
            # Handle violation
    """

    # Profanity and toxic language patterns
    PROFANITY_PATTERNS = [
        # Common profanity - keeping minimal for educational purposes
        r"\b(?:damn|hell|crap)\b",  # Mild
        # Add more patterns as needed for production
    ]

    # Harmful content patterns
    HARMFUL_PATTERNS = [
        (
            r"\b(?:kill|murder|harm|hurt)\s+(?:yourself|themselves|himself|herself)\b",
            "Self-harm or violence suggestion",
        ),
        (
            r"\b(?:suicide|self-harm)\s+(?:method|way|how)\b",
            "Suicide method discussion",
        ),
        (
            r"\bguarantee[ds]?\s+(?:cure|treatment|heal)\b",
            "Unverified medical guarantee",
        ),
    ]

    # Hate speech patterns
    HATE_PATTERNS = [
        (
            r"\b(?:all|every)\s+(?:\w+)\s+(?:are|is)\s+(?:stupid|dumb|inferior)\b",
            "Generalization/stereotyping",
        ),
    ]

    # Hallucination indicators - phrases that often precede fabricated info
    HALLUCINATION_INDICATORS = [
        r"according to (?:recent )?(?:studies|research|scientists)",
        r"research (?:has )?shows? that",
        r"studies (?:have )?(?:proven|confirmed|shown)",
        r"experts (?:agree|confirm|say)",
        r"it is (?:well-)?known that",
        r"statistics show",
        r"\d+%\s+of\s+(?:people|studies|experts)",
    ]

    # Confidence thresholds
    LOW_CONFIDENCE_THRESHOLD = 0.3
    HALLUCINATION_THRESHOLD = 0.5

    def __init__(
        self,
        enable_toxicity_filter: bool = True,
        enable_hallucination_filter: bool = True,
        toxicity_threshold: float = 0.5,
        hallucination_threshold: float = 0.5,
        strict_source_check: bool = True,
    ):
        """
        Initialize the output guard.

        Args:
            enable_toxicity_filter: Whether to check for toxic content
            enable_hallucination_filter: Whether to check for hallucinations
            toxicity_threshold: Score threshold for toxicity (0-1)
            hallucination_threshold: Score threshold for hallucination detection
            strict_source_check: Whether to verify cited sources exist
        """
        self.enable_toxicity_filter = enable_toxicity_filter
        self.enable_hallucination_filter = enable_hallucination_filter
        self.toxicity_threshold = toxicity_threshold
        self.hallucination_threshold = hallucination_threshold
        self.strict_source_check = strict_source_check

        # Pre-compile patterns
        self._compiled_profanity = [
            re.compile(p, re.IGNORECASE) for p in self.PROFANITY_PATTERNS
        ]
        self._compiled_harmful = [
            (re.compile(p, re.IGNORECASE), desc) for p, desc in self.HARMFUL_PATTERNS
        ]
        self._compiled_hate = [
            (re.compile(p, re.IGNORECASE), desc) for p, desc in self.HATE_PATTERNS
        ]
        self._compiled_hallucination = [
            re.compile(p, re.IGNORECASE) for p in self.HALLUCINATION_INDICATORS
        ]

    def validate(
        self,
        response: str,
        context_chunks: List[Dict[str, Any]],
        claimed_sources: Optional[List[str]] = None,
        confidence: Optional[str] = None,
    ) -> OutputValidationResult:
        """
        Validate LLM response.

        Args:
            response: The LLM's response text
            context_chunks: The retrieved context used for generation
            claimed_sources: Sources the response claims to use
            confidence: Confidence level from the response (high/medium/low)

        Returns:
            OutputValidationResult with validation status
        """
        violations = []
        violation_details = []
        confidence_score = 1.0

        # 1. Check for toxicity (most critical)
        if self.enable_toxicity_filter:
            toxicity_result = self._check_toxicity(response)
            if toxicity_result:
                violations.extend(toxicity_result[0])
                violation_details.extend(toxicity_result[1])
                # Toxic content is always blocked
                return OutputValidationResult(
                    passed=False,
                    violations=violations,
                    violation_details=violation_details,
                    original_response=response,
                )

        # 2. Check for hallucinations
        if self.enable_hallucination_filter:
            hallucination_result = self._check_hallucination(
                response, context_chunks, claimed_sources, confidence
            )
            if hallucination_result:
                violations.extend(hallucination_result[0])
                violation_details.extend(hallucination_result[1])
                confidence_score = hallucination_result[2]

                # If confidence is too low, flag but don't necessarily block
                if confidence_score < self.LOW_CONFIDENCE_THRESHOLD:
                    return OutputValidationResult(
                        passed=False,
                        violations=violations,
                        violation_details=violation_details,
                        confidence_score=confidence_score,
                        original_response=response,
                    )

        return OutputValidationResult(
            passed=True,
            violations=violations,
            violation_details=violation_details,
            confidence_score=confidence_score,
            original_response=response,
        )

    def _check_toxicity(self, text: str) -> Optional[tuple]:
        """Check for toxic content in response."""
        violations = []
        details = []

        # Check profanity
        for pattern in self._compiled_profanity:
            if pattern.search(text):
                violations.append(OutputViolationType.TOXICITY_PROFANITY)
                details.append("Profanity detected in response")
                break  # One profanity flag is enough

        # Check harmful content
        for pattern, desc in self._compiled_harmful:
            if pattern.search(text):
                violations.append(OutputViolationType.TOXICITY_HARMFUL)
                details.append(desc)

        # Check hate speech
        for pattern, desc in self._compiled_hate:
            if pattern.search(text):
                violations.append(OutputViolationType.TOXICITY_HATE)
                details.append(desc)

        return (violations, details) if violations else None

    def _check_hallucination(
        self,
        response: str,
        context_chunks: List[Dict[str, Any]],
        claimed_sources: Optional[List[str]],
        confidence: Optional[str],
    ) -> Optional[tuple]:
        """Check for potential hallucinations."""
        violations = []
        details = []
        confidence_score = 1.0

        # 1. Check if claimed sources exist in context
        if self.strict_source_check and claimed_sources:
            actual_sources = self._extract_sources(context_chunks)
            fabricated = self._find_fabricated_sources(claimed_sources, actual_sources)

            if fabricated:
                violations.append(OutputViolationType.HALLUCINATION_FABRICATED_SOURCE)
                details.append(f"Referenced non-existent sources: {fabricated}")
                confidence_score *= 0.5

        # 2. Check for unsupported statistical claims
        unsupported = self._check_unsupported_claims(response, context_chunks)
        if unsupported:
            violations.append(OutputViolationType.HALLUCINATION_UNSUPPORTED)
            details.extend(unsupported)
            confidence_score *= 0.7

        # 3. Check model's self-reported confidence
        if confidence:
            conf_lower = confidence.lower()
            if conf_lower == "low":
                violations.append(OutputViolationType.HALLUCINATION_LOW_CONFIDENCE)
                details.append("Model reported low confidence in response")
                confidence_score *= 0.5
            elif conf_lower == "medium":
                confidence_score *= 0.8

        # 4. Check for hallucination indicator phrases
        indicator_count = sum(
            1 for p in self._compiled_hallucination if p.search(response)
        )
        if indicator_count >= 2:  # Multiple indicators suggest potential issues
            confidence_score *= 0.8
            if indicator_count >= 3:
                violations.append(OutputViolationType.HALLUCINATION_UNSUPPORTED)
                details.append(
                    f"Multiple unverified claim indicators ({indicator_count})"
                )

        if violations:
            return (violations, details, confidence_score)
        return None

    def _extract_sources(self, context_chunks: List[Dict[str, Any]]) -> Set[str]:
        """Extract source names from context chunks."""
        sources = set()
        for chunk in context_chunks:
            metadata = chunk.get("metadata", {})
            source = metadata.get("source", "")
            if source:
                # Store both full name and without extension
                sources.add(source)
                sources.add(source.rsplit(".", 1)[0])
        return sources

    def _find_fabricated_sources(
        self, claimed: List[str], actual: Set[str]
    ) -> List[str]:
        """Find sources that were claimed but don't exist."""
        fabricated = []
        for source in claimed:
            source_clean = source.strip().lower()
            # Check if any actual source matches (fuzzy)
            if not any(
                source_clean in actual_src.lower() or actual_src.lower() in source_clean
                for actual_src in actual
            ):
                fabricated.append(source)
        return fabricated

    def _check_unsupported_claims(
        self, response: str, context_chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """Check for claims that aren't supported by context."""
        issues = []

        # Combine all context text
        context_text = " ".join(
            chunk.get("text", "") for chunk in context_chunks
        ).lower()

        # Check for specific statistical claims
        stat_pattern = re.compile(r"(\d+(?:\.\d+)?)\s*%", re.IGNORECASE)
        response_stats = stat_pattern.findall(response)
        context_stats = stat_pattern.findall(context_text)

        for stat in response_stats:
            if stat not in context_stats:
                issues.append(f"Statistic '{stat}%' not found in source context")

        # Check for specific numeric claims
        num_pattern = re.compile(
            r"\b(\d{2,})\s+(?:people|cases|deaths|patients)", re.IGNORECASE
        )
        response_nums = num_pattern.findall(response)
        context_nums = num_pattern.findall(context_text)

        for num in response_nums:
            if num not in context_nums:
                issues.append(f"Numeric claim '{num}' not found in source context")

        return issues[:3]  # Limit to top 3 issues


if __name__ == "__main__":
    # Test the output guard
    guard = OutputGuard()

    # Sample context
    sample_context = [
        {
            "text": "AQI above 150 is considered unhealthy for sensitive groups. "
            "Children, elderly, and people with respiratory conditions should limit outdoor exposure.",
            "metadata": {"source": "health_precautions.txt"},
        },
        {
            "text": "PM2.5 is the most harmful pollutant in urban areas. "
            "It can penetrate deep into the lungs and bloodstream.",
            "metadata": {"source": "pollutants_guide.txt"},
        },
    ]

    test_cases = [
        # Normal response (should pass)
        {
            "response": "When AQI is above 150, it's considered unhealthy for sensitive groups. "
            "You should limit outdoor exposure, especially if you have respiratory conditions.",
            "sources": ["health_precautions.txt"],
            "confidence": "high",
        },
        # Fabricated source (should flag)
        {
            "response": "According to the EPA guidelines, AQI above 150 requires immediate evacuation.",
            "sources": ["epa_guidelines.txt", "health_precautions.txt"],
            "confidence": "high",
        },
        # Made up statistics (should flag)
        {
            "response": "Studies show that 85% of people experience symptoms when AQI reaches 150.",
            "sources": ["health_precautions.txt"],
            "confidence": "medium",
        },
        # Low confidence (should flag)
        {
            "response": "I'm not sure, but AQI 150 might be harmful.",
            "sources": [],
            "confidence": "low",
        },
    ]

    print("=" * 60)
    print("OUTPUT GUARD TEST")
    print("=" * 60)

    for i, test in enumerate(test_cases):
        result = guard.validate(
            response=test["response"],
            context_chunks=sample_context,
            claimed_sources=test["sources"],
            confidence=test["confidence"],
        )

        status = "✅ PASS" if result.passed else "⚠️ FLAG"
        print(f"\n{status} Test {i+1}:")
        print(f"   Response: {test['response'][:60]}...")
        print(f"   Confidence Score: {result.confidence_score:.2f}")
        if result.violations:
            print(f"   Violations: {[v.value for v in result.violations]}")
            print(f"   Details: {result.violation_details}")

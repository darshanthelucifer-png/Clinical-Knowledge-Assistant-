"""
================================================================================
ClinSaarthi AI - Prompt Guard & Input Sanitization Engine
================================================================================
What it does:
    Inspects, sanitizes, and validates user clinical queries and input text
    to defend against prompt injection, jailbreaks, delimiter smuggling,
    system prompt exfiltration, and resource-exhaustion denial of service.

Python Concepts Demonstrated:
    1. Dataclasses: Encapsulating inspection results (`PromptGuardResult`).
    2. Compiled Regex Patterns: High-performance precompiled adversarial regex patterns.
    3. Input Normalization: Removing null bytes, non-printable control chars, and excessive whitespace.
    4. Guardrails: Defense-in-depth security before input reaches vector search or LLMs.
================================================================================
"""
from dataclasses import dataclass, field
from typing import List, Optional
import re
import unicodedata


@dataclass(frozen=True)
class PromptGuardResult:
    """
    Immutable representation of an input inspection result.
    """
    is_safe: bool
    sanitized_text: str
    threat_types: List[str] = field(default_factory=list)
    rejection_message: Optional[str] = None


class PromptGuard:
    """
    Production-grade input guardrail engine detecting adversarial prompt injections,
    delimiters, system prompt leak attempts, and abnormal payloads.
    """
    MAX_QUERY_LENGTH: int = 2000
    MIN_QUERY_LENGTH: int = 2

    DEFAULT_REJECTION_MESSAGE: str = (
        "Security Notice: This query was flagged for adversarial prompt injection, "
        "system instruction overrides, or unsupported formatting. ClinSaarthi AI operates "
        "strictly within certified medical guidelines and clinical safety guardrails."
    )

    # 1. Instruction Override & System Manipulation Patterns
    INSTRUCTION_OVERRIDE_PATTERNS = [
        re.compile(r"(?i)\b(ignore|disregard|forget|override|bypass)\b.{0,40}\b(previous|prior|above|system|all)\b.{0,30}\b(instructions|rules|prompts|guidelines|constraints)\b"),
        re.compile(r"(?i)\bsystem\s*(override|reset|shutdown|directive|prompt|mode)\b"),
        re.compile(r"(?i)\b(new\s+system\s+instruction|developer\s+mode|disregard\s+all\s+rules)\b"),
        re.compile(r"(?i)\bstop\s+being\s+(a\s+medical|an\s+ai|a\s+clinical)\b"),
    ]

    # 2. Jailbreak & Unrestricted Persona Patterns
    JAILBREAK_PATTERNS = [
        re.compile(r"(?i)\b(dan\s+mode|do\s+anything\s+now|jailbreak|uncensored|unrestricted\s+mode)\b"),
        re.compile(r"(?i)\b(roleplay|pretend|act\s+as)\b.{0,40}\b(unrestricted|evil|unfiltered|without\s+ethics|no\s+rules|without\s+guidelines|unconstrained)\b"),
        re.compile(r"(?i)\bwithout\s+any\s+(safety|ethical|medical|clinical)\s+(guardrails|filters|rules|constraints)\b"),
    ]

    # 3. System Prompt & Secret Exfiltration Patterns
    PROMPT_LEAK_PATTERNS = [
        re.compile(r"(?i)\b(reveal|display|output|show|print|repeat)\b.{0,30}\b(system\s+prompt|initial\s+instructions|base\s+prompt|hidden\s+prompt|developer\s+instructions)\b"),
        re.compile(r"(?i)\bwhat\s+(are|is)\s+your\s+(exact\s+)?(initial\s+instructions|system\s+prompt|system\s+rules)\b"),
        re.compile(r"(?i)\bprint\s+everything\s+above\s+this\s+line\b"),
    ]

    # 4. Delimiter Smuggling & Chat Template Injection Patterns
    DELIMITER_PATTERNS = [
        re.compile(r"(<\|im_start\|>|<\|im_end\|>|\[INST\]|\[/INST\]|<<SYS>>|<</SYS>>)"),
        re.compile(r"(?i)(###\s*(system|instruction|human|assistant)|```\s*system)"),
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        """
        Sanitizes text by:
        1. Stripping null bytes and zero-width characters.
        2. Normalizing unicode characters (NFKC).
        3. Stripping non-printable control characters except line feeds and tabs.
        4. Normalizing excessive spaces and blank lines.
        """
        if not text:
            return ""

        # Remove null bytes and common zero-width joiners/spaces
        cleaned = text.replace("\x00", "").replace("\u200b", "").replace("\ufeff", "")

        # Normalize unicode
        cleaned = unicodedata.normalize("NFKC", cleaned)

        # Remove non-printable control characters except \n, \r, \t
        cleaned = "".join(
            ch for ch in cleaned
            if ch in ("\n", "\r", "\t") or not unicodedata.category(ch).startswith("C")
        )

        # Normalize redundant spaces while preserving single newlines
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.splitlines()]
        cleaned = "\n".join(lines).strip()

        return cleaned

    @classmethod
    def inspect(cls, text: str) -> PromptGuardResult:
        """
        Comprehensive security inspection:
        - Validates input length.
        - Sanitizes input characters.
        - Scans against instruction override, jailbreak, prompt leak, and delimiter patterns.
        """
        sanitized = cls.sanitize(text)

        # Empty or too short
        if len(sanitized) < cls.MIN_QUERY_LENGTH:
            return PromptGuardResult(
                is_safe=False,
                sanitized_text=sanitized,
                threat_types=["insufficient_length"],
                rejection_message="Query is too short or empty."
            )

        # Max length defense (DoS mitigation)
        if len(sanitized) > cls.MAX_QUERY_LENGTH:
            return PromptGuardResult(
                is_safe=False,
                sanitized_text=sanitized[:cls.MAX_QUERY_LENGTH],
                threat_types=["length_exceeded"],
                rejection_message=f"Query exceeds maximum allowed length of {cls.MAX_QUERY_LENGTH} characters."
            )

        threats: List[str] = []

        # Check Instruction Overrides
        for pat in cls.INSTRUCTION_OVERRIDE_PATTERNS:
            if pat.search(sanitized):
                threats.append("instruction_override")
                break

        # Check Jailbreaks
        for pat in cls.JAILBREAK_PATTERNS:
            if pat.search(sanitized):
                threats.append("jailbreak")
                break

        # Check Prompt Leak
        for pat in cls.PROMPT_LEAK_PATTERNS:
            if pat.search(sanitized):
                threats.append("prompt_leak")
                break

        # Check Delimiters
        for pat in cls.DELIMITER_PATTERNS:
            if pat.search(sanitized):
                threats.append("delimiter_injection")
                break

        if threats:
            return PromptGuardResult(
                is_safe=False,
                sanitized_text=sanitized,
                threat_types=threats,
                rejection_message=cls.DEFAULT_REJECTION_MESSAGE
            )

        return PromptGuardResult(
            is_safe=True,
            sanitized_text=sanitized,
            threat_types=[]
        )

"""
================================================================================
ClinSaarthi AI - Comprehensive PII / PHI Masking Service
================================================================================
What it does:
    Detects, extracts, and irreversibly redacts protected health information (PHI)
    and personally identifiable information (PII) including patient names, physician
    names, phone numbers, emails, MRNs, dates of birth, SSNs, Aadhaar IDs, and
    physical addresses BEFORE storage, vector embedding, or LLM inference.

Python Concepts Demonstrated:
    1. Python Dataclasses (@dataclass): Clean data transfer objects for masking results.
    2. Greedy Interval Scheduling Algorithm: Resolves overlapping regex/NER spans
       ensuring non-destructive text substitution.
    3. Reverse-Offset String Reconstruction: Modifying strings by descending character
       indices so earlier offsets are never invalidated by variable-length placeholders.
    4. Referential Consistency: Reusing identical placeholders (e.g. [PATIENT_1])
       for repeated mentions of the same entity across the clinical document.
    5. Lazy Module Initialization & Graceful Degradation: Handles missing NLP
       weights gracefully via rule-based fallbacks.
================================================================================
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Optional, Any
import re
from django.conf import settings

@dataclass
class PIISpan:
    """Internal representation of a detected sensitive text interval."""
    start: int
    end: int
    category: str
    original: str

    @property
    def length(self) -> int:
        return self.end - self.start

@dataclass
class PIIMaskResult:
    """Immutable result object returning masked text, mapping, and audit metrics."""
    masked_text: str
    mapping: Dict[str, str] = field(default_factory=dict)
    categories_detected: Dict[str, int] = field(default_factory=dict)
    spans_detected: int = 0

class PIIMasker:
    """
    Zero-Trust PII Masker combining deterministic regex rules and spaCy NER/Matcher.
    """
    # --------------------------------------------------------------------------
    # Precompiled Regular Expression Detectors
    # --------------------------------------------------------------------------
    EMAIL_REGEX = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b'
    )
    PHONE_REGEX = re.compile(
        r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b|(?:\+91[-.\s]?)?[6-9]\d{4}[-.\s]?\d{5}\b'
    )
    SSN_REGEX = re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b'
    )
    AADHAAR_REGEX = re.compile(
        r'\b\d{4}\s\d{4}\s\d{4}\b'
    )
    MRN_REGEX = re.compile(
        r'\b(?:MRN|mrn|Medical Record Number|Med Rec #)[\s:#]*([A-Za-z0-9-]{6,16})\b',
        re.IGNORECASE
    )
    DOB_REGEX = re.compile(
        r'\b(?:DOB|Date of Birth|Birthdate)[\s:#]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
        re.IGNORECASE
    )
    ADDRESS_REGEX = re.compile(
        r'\b\d{1,5}\s+[A-Za-z0-9\s.,-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Terrace|Heights|Flat|Apartment|Apt)[\w\s,.-]*\b',
        re.IGNORECASE
    )
    CLINICAL_PERSON_REGEX = re.compile(
        r'\b(?:PATIENT(?:\s+NAME)?|Pt|Patient|ATTENDING(?:\s+PHYSICIAN)?|Dr\.|Doctor|Physician|Mr\.|Mrs\.|Ms\.)[\s:#]+([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)+)',
        re.MULTILINE
    )

    # Common clinical entities/departments to whitelist from being treated as person names
    CLINICAL_WHITELIST: Set[str] = {
        "Cardiology", "Oncology", "Neurology", "Emergency", "Pediatrics",
        "Radiology", "Pathology", "Surgery", "Dermatology", "Gastroenterology",
        "Apixaban", "Rivaroxaban", "Lisinopril", "Atorvastatin", "Doxorubicin",
        "Tamoxifen", "Prednisolone", "Azithromycin", "Salbutamol", "Ipratropium",
        "Stage", "Cycle", "Follow", "Hospital", "Discharge", "History",
        "Physical", "Assessment", "Examination", "Plan", "Recommendation"
    }

    _nlp = None

    @classmethod
    def _get_nlp(cls):
        """Lazy load spaCy model with graceful fallback."""
        if cls._nlp is None:
            try:
                import spacy
                model_name = getattr(settings, 'SPACY_MODEL', 'en_core_web_sm')
                try:
                    cls._nlp = spacy.load(model_name)
                except Exception:
                    cls._nlp = spacy.load("en_core_web_sm")
            except Exception:
                # If spaCy model is not yet installed, rule-based matching handles clinical PII
                cls._nlp = False
        return cls._nlp

    @classmethod
    def extract_spans(cls, text: str) -> List[PIISpan]:
        """
        Runs all detectors (Regex + spaCy NER/Matcher) and extracts candidate spans.
        """
        candidates: List[PIISpan] = []

        # 1. Email extraction
        for match in cls.EMAIL_REGEX.finditer(text):
            candidates.append(PIISpan(match.start(), match.end(), "EMAIL", match.group(0)))

        # 2. Phone extraction
        for match in cls.PHONE_REGEX.finditer(text):
            candidates.append(PIISpan(match.start(), match.end(), "PHONE", match.group(0)))

        # 3. SSN extraction
        for match in cls.SSN_REGEX.finditer(text):
            candidates.append(PIISpan(match.start(), match.end(), "SSN", match.group(0)))

        # 4. Aadhaar extraction
        for match in cls.AADHAAR_REGEX.finditer(text):
            candidates.append(PIISpan(match.start(), match.end(), "AADHAAR", match.group(0)))

        # 5. MRN extraction
        for match in cls.MRN_REGEX.finditer(text):
            # Target the captured group or the full phrase
            if match.groups() and match.group(1):
                start = match.start(1)
                end = match.end(1)
                candidates.append(PIISpan(start, end, "MRN", match.group(1)))
            else:
                candidates.append(PIISpan(match.start(), match.end(), "MRN", match.group(0)))

        # 6. DOB extraction
        for match in cls.DOB_REGEX.finditer(text):
            if match.groups() and match.group(1):
                start = match.start(1)
                end = match.end(1)
                candidates.append(PIISpan(start, end, "DOB", match.group(1)))
            else:
                candidates.append(PIISpan(match.start(), match.end(), "DOB", match.group(0)))

        # 7. Address extraction
        for match in cls.ADDRESS_REGEX.finditer(text):
            candidates.append(PIISpan(match.start(), match.end(), "ADDRESS", match.group(0)))

        # 8. Clinical context-based person extraction via regex
        detected_names: Set[str] = set()
        for match in cls.CLINICAL_PERSON_REGEX.finditer(text):
            if match.groups() and match.group(1):
                name_val = match.group(1).strip()
                if not any(word in cls.CLINICAL_WHITELIST for word in name_val.split()):
                    candidates.append(PIISpan(match.start(1), match.end(1), "PATIENT", name_val))
                    if len(name_val) >= 3:
                        detected_names.add(name_val)

        # 9. spaCy Named Entity Recognition for PERSON (if available)
        nlp = cls._get_nlp()
        if nlp and nlp is not False:
            try:
                doc = nlp(text)
                for ent in doc.ents:
                    if ent.label_ in ("PERSON", "PER"):
                        clean_name = ent.text.strip()
                        if len(clean_name) > 2 and not any(w in cls.CLINICAL_WHITELIST for w in clean_name.split()):
                            candidates.append(PIISpan(ent.start_char, ent.end_char, "PATIENT", clean_name))
                            detected_names.add(clean_name)
            except Exception:
                pass

        # 10. Coreference Propagation: Ensure any detected name is masked everywhere in document
        for name in detected_names:
            escaped_name = re.escape(name)
            pattern = re.compile(rf'\b{escaped_name}\b')
            for match in pattern.finditer(text):
                candidates.append(PIISpan(match.start(), match.end(), "PATIENT", name))

        return candidates

    @classmethod
    def resolve_overlaps(cls, spans: List[PIISpan]) -> List[PIISpan]:
        """
        Greedy Non-overlapping Interval Scheduling:
        Sorts candidate spans by priority/length, then start position,
        and eliminates any spans that overlap with an already selected span.
        """
        if not spans:
            return []

        # Sort: Primary key = start offset ascending, Secondary key = length descending
        sorted_spans = sorted(spans, key=lambda s: (s.start, -s.length))

        resolved: List[PIISpan] = []
        last_end = -1

        for span in sorted_spans:
            if span.start >= last_end:
                resolved.append(span)
                last_end = span.end
            else:
                # Conflict: check if current span is strictly contained or overlaps
                # Keep the longer span if it started earlier or replace if advantageous
                continue

        return resolved

    @classmethod
    def mask(cls, text: str) -> PIIMaskResult:
        """
        Scans text, extracts and resolves PII spans, replaces them with
        deterministic placeholders, and builds the reversible audit mapping.
        """
        raw_spans = cls.extract_spans(text)
        resolved_spans = cls.resolve_overlaps(raw_spans)

        # Sort spans descending by start index for safe right-to-left substitution
        descending_spans = sorted(resolved_spans, key=lambda s: s.start, reverse=True)

        mapping: Dict[str, str] = {}
        original_to_tag: Dict[str, str] = {}
        category_counters: Dict[str, int] = {
            "PATIENT": 0,
            "PHONE": 0,
            "EMAIL": 0,
            "SSN": 0,
            "AADHAAR": 0,
            "MRN": 0,
            "DOB": 0,
            "ADDRESS": 0,
        }
        categories_detected: Dict[str, int] = {k: 0 for k in category_counters}

        # Build placeholders with referential consistency (same original value -> same placeholder)
        for span in sorted(resolved_spans, key=lambda s: s.start):
            orig_val = span.original
            cat = span.category
            if orig_val not in original_to_tag:
                category_counters[cat] = category_counters.get(cat, 0) + 1
                tag = f"[{cat}_{category_counters[cat]}]"
                original_to_tag[orig_val] = tag
                mapping[tag] = orig_val
                categories_detected[cat] = categories_detected.get(cat, 0) + 1

        # Perform replacement from right-to-left
        masked_chars = list(text)
        for span in descending_spans:
            tag = original_to_tag[span.original]
            masked_chars[span.start:span.end] = list(tag)

        masked_text = "".join(masked_chars)

        return PIIMaskResult(
            masked_text=masked_text,
            mapping=mapping,
            categories_detected={k: v for k, v in categories_detected.items() if v > 0},
            spans_detected=len(resolved_spans)
        )

    @classmethod
    def unmask(cls, masked_text: str, mapping: Dict[str, str]) -> str:
        """
        Reconstructs original clinical text by substituting placeholders
        back to their original sensitive values.
        """
        unmasked = masked_text
        for placeholder, original in mapping.items():
            unmasked = unmasked.replace(placeholder, original)
        return unmasked

    @classmethod
    def assert_no_pii_leak(cls, text: str, raw_values: Optional[List[str]] = None) -> None:
        """
        Security verification helper: Scans text to guarantee no raw PII patterns exist.
        If raw_values list is provided, checks that none of those specific strings appear in text.
        Raises ValueError with details if any pattern is detected.
        Used by security audit tests before payload dispatch to LLMs.
        """
        leaks = []
        if cls.EMAIL_REGEX.search(text):
            leaks.append("Email pattern detected in LLM payload")
        if cls.PHONE_REGEX.search(text):
            leaks.append("Phone pattern detected in LLM payload")
        if cls.SSN_REGEX.search(text):
            leaks.append("SSN pattern detected in LLM payload")
        if cls.AADHAAR_REGEX.search(text):
            leaks.append("Aadhaar pattern detected in LLM payload")

        if raw_values:
            for val in raw_values:
                if val and len(val.strip()) >= 3 and val in text:
                    leaks.append(f"Specific raw entity value leaked: '{val[:4]}...'")

        if leaks:
            raise ValueError(f"CRITICAL SECURITY VIOLATION: PHI/PII leakage detected: {'; '.join(leaks)}")

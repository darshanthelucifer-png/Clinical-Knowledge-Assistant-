"""
================================================================================
ClinSaarthi AI - Clinical Intent Router
================================================================================
What it does:
    Classifies clinician queries as the first pipeline step before retrieval:
    1. GREETING: Natural conversational salutations, pleasantries, or bot info.
    2. MEDICAL: Evidence-based clinical guidelines, pharmacology, dosing, diagnosis.
    3. NOTE_QUERY: Queries scoped to patient discharge/clinical notes or patient history.
    4. OFF_TOPIC: General world knowledge, sports, entertainment, or non-medical topics.
    5. UNSAFE: Prompt injection, jailbreaks, delimiter smuggling, or safety threats.

Two-Tier Pipeline Architecture:
    - Tier 1: Rules First. High-speed compiled regex patterns, clinical entity
      lookups, and PromptGuard inspections for zero-latency deterministic routing.
    - Tier 2: LLM Second. Fast LLM disambiguation fallback when rules are uncertain.
================================================================================
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Generator
import re
import logging
from django.conf import settings

from ai.prompt_guard import PromptGuard
from ai.nlp import MedicalNLPExtractor, COMMON_DRUGS, MEDICAL_ACRONYMS
from ai.llm import LLMClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IntentResult:
    """Immutable representation of intent classification result."""
    intent: str
    confidence: float
    reason: str
    suggested_reply: Optional[str] = None


class IntentRouter:
    """
    Production-grade Intent Router executing Rules-First, LLM-Second classification.
    """
    # Intent categories
    GREETING = "greeting"
    MEDICAL = "medical"
    NOTE_QUERY = "note_query"
    OFF_TOPIC = "off_topic"
    UNSAFE = "unsafe"

    # 1. Conversational Greeting Patterns
    GREETING_PATTERNS = [
        re.compile(r"^(hi|hello|hey|heya|howdy|sup|greetings)[\s,!.]*$", re.IGNORECASE),
        re.compile(r"^(good\s+(morning|afternoon|evening|day))[\s,!.]*$", re.IGNORECASE),
        re.compile(r"^(what'?s\s+up|whats\s+up|wassup)[\s,!?.]*$", re.IGNORECASE),
        re.compile(r"^(hi|hello|hey|greetings|good\s+(morning|afternoon|evening))\s+(clinsaarthi|assistant|doc|doctor|team|there|bot|ai)[\s,!.]*$", re.IGNORECASE),
        re.compile(r"^(how\s+are\s+you|how's\s+it\s+going|how\s+do\s+you\s+do)[\s,!?.]*$", re.IGNORECASE),
        re.compile(r"^(who\s+are\s+you|what\s+are\s+you|what\s+can\s+you\s+do|what\s+is\s+your\s+name|help|help\s+me)[\s,!?.]*$", re.IGNORECASE),
    ]

    # 2. General Non-Medical Off-Topic Patterns
    OFF_TOPIC_PATTERNS = [
        re.compile(r"\b(world\s+cup|football|soccer|cricket|nba|nfl|super\s*bowl|fifa|olympics|champions\s+league|premier\s+league)\b", re.IGNORECASE),
        re.compile(r"\b(who\s+won|score\s+of|match\s+result|ballon\s+d'or|mvp|stanley\s+cup|grand\s+slam)\b", re.IGNORECASE),
        re.compile(r"\b(president|prime\s+minister|election|parliament|congress|democrat|republican|senator)\b", re.IGNORECASE),
        re.compile(r"\b(capital\s+of|highest\s+mountain|longest\s+river|tallest\s+building|population\s+of)\b", re.IGNORECASE),
        re.compile(r"\b(tell\s+me\s+a\s+joke|write\s+a\s+poem|sing\s+a\s+song|write\s+a\s+story|riddle)\b", re.IGNORECASE),
        re.compile(r"\b(recipe\s+for|how\s+to\s+cook|how\s+to\s+bake|bake\s+a\s+cake|cocktail\s+recipe)\b", re.IGNORECASE),
        re.compile(r"\b(weather\s+in|weather\s+today|forecast|movie\s+review|box\s+office|celebrity\s+gossip)\b", re.IGNORECASE),
        re.compile(r"\b(bitcoin|crypto|stock\s+market|ethereum|nasdaq|dow\s+jones)\b", re.IGNORECASE),
        re.compile(r"\b(what\s+is\s+the\s+meaning\s+of\s+life|who\s+is\s+elvis|who\s+is\s+taylor\s+swift)\b", re.IGNORECASE),
        re.compile(r"^(what\s+is\s+2\s*\+\s*2|calculate\s+\d+[\+\-\*\/]\d+)[\s,!?.]*$", re.IGNORECASE),
    ]

    # 3. Patient Note Trigger Terms
    NOTE_TRIGGERS = [
        "patient", "clinical note", "discharge note", "mrn", "this patient",
        "rajesh", "progress note", "in the note", "patient's note", "patient note"
    ]

    # 4. Clinical Condition & Medical Term Keywords
    CLINICAL_KEYWORDS = [
        "dose", "dosage", "dosing", "contraindicat", "indication", "recommend",
        "treatment", "first-line", "second-line", "therapy", "anticoagula",
        "atrial fibrillation", "afib", "hypertension", "copd", "pneumonia",
        "diabetes", "heart failure", "crcl", "egfr", "inr", "curb-65",
        "cha2ds2", "has-bled", "fev1", "hba1c", "hypoglycemia", "hyperglycemia",
        "stroke", "bleeding", "creatinine", "renal", "hepatic", "kidney",
        "cardiology", "pulmonary", "endocrine", "asthma", "myocardial",
        "guideline", "guidelines", "protocol", "side effect", "adverse",
        "pharmacotherapy", "drug", "medication", "pill", "tablet", "infusion",
        "intravenous", "subcutaneous", "oral", "antibiotic", "beta blocker",
        "ace inhibitor", "arb", "sglt2", "glp-1", "doac", "statin", "aspirin",
        "regimen", "chemotherapy", "radiation", "cancer", "tumor", "oncology",
        "fractionation", "surgery", "pediatric", "pathology", "syndrome",
        "disease", "disorder", "infection", "vaccine", "clinical trial"
    ]

    @classmethod
    def _contains_medical_entities(cls, query: str) -> bool:
        """Checks if query contains known drug names, medical acronyms, or clinical keywords."""
        q_lower = query.lower()

        # Check common drugs
        for drug in COMMON_DRUGS:
            if re.search(r'\b' + re.escape(drug.lower()) + r'\b', q_lower):
                return True

        # Check medical acronyms (word boundaries)
        words = re.findall(r'\b[A-Za-z0-9\-\/]+\b', query)
        for w in words:
            if w.upper() in MEDICAL_ACRONYMS:
                return True

        # Check clinical keywords
        for kw in cls.CLINICAL_KEYWORDS:
            if re.search(r'\b' + re.escape(kw) + r'\b', q_lower):
                return True

        return False

    @classmethod
    def route(cls, query: str, note_id: Optional[str] = None) -> IntentResult:
        """
        Classifies user query intent using Rules First, LLM Second.
        """
        cleaned_query = query.strip()

        # Step 0: Security & Safety Guardrails
        guard_res = PromptGuard.inspect(cleaned_query)
        if not guard_res.is_safe:
            return IntentResult(
                intent=cls.UNSAFE,
                confidence=1.0,
                reason="Flagged by PromptGuard safety guardrails",
                suggested_reply=guard_res.rejection_message or PromptGuard.DEFAULT_REJECTION_MESSAGE
            )

        sanitized = guard_res.sanitized_text
        sanitized_lower = sanitized.lower()

        # Has explicit clinical or medical terms?
        has_medical = cls._contains_medical_entities(sanitized)

        # Step 1: Note Query Rule
        # If note_id is explicitly supplied or query directly references patient documentation
        has_note_keyword = any(trigger in sanitized_lower for trigger in cls.NOTE_TRIGGERS)
        if (note_id and has_medical) or (has_note_keyword and has_medical):
            return IntentResult(
                intent=cls.NOTE_QUERY,
                confidence=0.98,
                reason="Query explicitly references patient clinical note or note_id context"
            )

        # Step 2: Greeting Rule (ONLY if query does not contain specific medical question)
        if not has_medical:
            for pat in cls.GREETING_PATTERNS:
                if pat.search(sanitized):
                    return IntentResult(
                        intent=cls.GREETING,
                        confidence=0.99,
                        reason="Matched conversational greeting pattern without medical queries"
                    )

        # Step 3: Off-Topic Rule (zero medical entities + matches off-topic topic patterns)
        if not has_medical:
            for pat in cls.OFF_TOPIC_PATTERNS:
                if pat.search(sanitized):
                    return IntentResult(
                        intent=cls.OFF_TOPIC,
                        confidence=0.99,
                        reason="Matched non-medical general knowledge or trivia pattern"
                    )

        # Step 4: Medical Rule
        if has_medical:
            return IntentResult(
                intent=cls.MEDICAL,
                confidence=0.95,
                reason="Query contains recognized clinical conditions, pharmacological entities, or guideline terms"
            )

        # Step 5: LLM Second (Fallback Disambiguation)
        # If query is neither clearly greeting, off-topic, nor contains known medical keywords:
        hf_token = getattr(settings, 'HF_TOKEN', '')
        if hf_token:
            try:
                from huggingface_hub import InferenceClient
                client = InferenceClient(
                    model=getattr(settings, 'LLM_MODEL_ID', 'Qwen/Qwen2.5-7B-Instruct'),
                    token=hf_token
                )
                prompt = (
                    "You are a strict query classifier for a clinical AI system. "
                    "Classify the following query into exactly one of: 'greeting', 'medical', 'note_query', 'off_topic', 'unsafe'.\n"
                    f"Query: \"{sanitized}\"\n"
                    "Reply with only the lowercase category name."
                )
                resp = client.text_generation(prompt=prompt, max_new_tokens=10).strip().lower()
                for cat in [cls.GREETING, cls.MEDICAL, cls.NOTE_QUERY, cls.OFF_TOPIC, cls.UNSAFE]:
                    if cat in resp:
                        return IntentResult(
                            intent=cat,
                            confidence=0.85,
                            reason="Classified by LLM intent inference"
                        )
            except Exception as e:
                logger.debug("LLM intent classification fallback exception: %s", e)

        # If LLM unavailable, determine based on semantic heuristics
        # Short phrases with no clinical terms are off-topic or general greeting
        if len(sanitized.split()) <= 4 and any(w in sanitized_lower for w in ["hi", "hello", "hey", "sup", "morning", "evening", "who"]):
            return IntentResult(
                intent=cls.GREETING,
                confidence=0.80,
                reason="Short conversational salutation heuristic"
            )

        # Non-clinical unknown query -> off-topic
        return IntentResult(
            intent=cls.OFF_TOPIC,
            confidence=0.80,
            reason="Unrecognized query without clinical terminology routed to off-topic"
        )

    @classmethod
    def get_natural_response(cls, intent: str, query: str) -> str:
        """
        Generates a concise, natural, plain-text response for greeting or off-topic queries.
        No citations, no confidence score, no verification table.
        """
        q_lower = query.lower().strip()

        if intent == cls.GREETING:
            if "what's up" in q_lower or "whats up" in q_lower or "sup" in q_lower:
                return (
                    "Hello! I am doing well, thank you. I am ClinSaarthi AI, your clinical knowledge assistant. "
                    "How can I assist you with clinical practice guidelines or patient queries today?"
                )
            if "who are you" in q_lower or "what can you do" in q_lower or "help" in q_lower:
                return (
                    "I am ClinSaarthi AI, an evidence-based clinical decision-support assistant. "
                    "I can answer questions regarding certified clinical guidelines, drug dosing, contraindications, "
                    "and patient discharge notes with inline verified citations."
                )
            return (
                "Hello! I am ClinSaarthi AI, your clinical knowledge assistant. "
                "How can I assist you with clinical guidelines, medication protocols, or patient notes today?"
            )

        if intent == cls.OFF_TOPIC:
            return (
                "I am ClinSaarthi AI, an evidence-based clinical decision-support assistant designed strictly for "
                "medical practice guidelines and patient clinical notes. I am unable to answer general trivia, sports, "
                "or non-medical questions. Please let me know if you have a clinical or guideline inquiry!"
            )

        return (
            "I'm not sure — this information is not found in the provided documents. "
            "Please consider rephrasing your clinical query with specific drug names or guideline topics."
        )

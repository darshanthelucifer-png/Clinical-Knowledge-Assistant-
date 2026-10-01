"""
================================================================================
ClinSaarthi AI - Medical NLP, Acronym Expansion & Entity Extraction Pipeline
================================================================================
What it does:
    1. Acronym & Abbreviation Expansion: Resolves common clinical abbreviations
       (e.g., AF -> Atrial Fibrillation, DOAC -> Direct Oral Anticoagulant) to improve
       dense & sparse retrieval recall.
    2. Clinical Intent Classification: Identifies clinician intent (dosing,
       contraindication, treatment, diagnosis, monitoring) to tune answering strategy.
    3. Pharmacological Entity Extraction: Parses drug names, dosages, units,
       routes, and frequencies from answers and source passages for factual verification.

Python Concepts Demonstrated:
    1. Regular Expressions & Lookarounds: Robust parsing of complex clinical dosages
       and medication nomenclature without relying on fragile external DLL dependencies.
    2. Intent Mapping / Rule-Based Classification: Fast, deterministic semantic tagging
       with zero inference latency.
================================================================================
"""
import re
from typing import List, Dict, Any, Tuple, Optional

# Comprehensive medical abbreviation dictionary
MEDICAL_ACRONYMS: Dict[str, str] = {
    "AF": "Atrial Fibrillation",
    "AFIB": "Atrial Fibrillation",
    "DOAC": "Direct Oral Anticoagulant",
    "DOACS": "Direct Oral Anticoagulants",
    "NOAC": "Novel Oral Anticoagulant",
    "NOACS": "Novel Oral Anticoagulants",
    "OAC": "Oral Anticoagulation",
    "VKA": "Vitamin K Antagonist",
    "MI": "Myocardial Infarction",
    "HTN": "Hypertension",
    "DVT": "Deep Vein Thrombosis",
    "PE": "Pulmonary Embolism",
    "CKD": "Chronic Kidney Disease",
    "ESRD": "End-Stage Renal Disease",
    "HF": "Heart Failure",
    "CHF": "Congestive Heart Failure",
    "HFEPEF": "Heart Failure with Preserved Ejection Fraction",
    "HFREF": "Heart Failure with Reduced Ejection Fraction",
    "LVEF": "Left Ventricular Ejection Fraction",
    "T2DM": "Type 2 Diabetes Mellitus",
    "STEMI": "ST-Elevation Myocardial Infarction",
    "NSTEMI": "Non-ST-Elevation Myocardial Infarction",
    "CAD": "Coronary Artery Disease",
    "INR": "International Normalized Ratio",
    "CRCL": "Creatinine Clearance",
    "EGFR": "Estimated Glomerular Filtration Rate",
    "ACEI": "ACE Inhibitor",
    "ARB": "Angiotensin Receptor Blocker",
    "BB": "Beta Blocker",
    "CCB": "Calcium Channel Blocker",
    "TIA": "Transient Ischemic Attack",
    "COPD": "Chronic Obstructive Pulmonary Disease",
}

# Common clinical medications across cardiology, internal medicine, emergency, oncology
COMMON_DRUGS = [
    "Rivaroxaban", "Apixaban", "Dabigatran", "Edoxaban", "Warfarin",
    "Amiodarone", "Metoprolol", "Diltiazem", "Digoxin", "Verapamil",
    "Bisoprolol", "Carvedilol", "Atorvastatin", "Rosuvastatin", "Aspirin",
    "Clopidogrel", "Ticagrelor", "Heparin", "Enoxaparin", "Fondaparinux",
    "Lisinopril", "Ramipril", "Losartan", "Valsartan", "Sacubitril", "Amlodipine",
    "Furosemide", "Spironolactone", "Eplerenone", "Empagliflozin", "Dapagliflozin",
    "Semaglutide", "Metformin", "Insulin", "Levothyroxine", "Omeprazole", "Pantoprazole",
    "Tiotropium", "Formoterol", "Prednisone", "Amoxicillin", "Azithromycin", "Doxycycline",
    "Cisplatin", "Paclitaxel", "Pembrolizumab", "Trastuzumab", "Doxorubicin"
]

# Regex building blocks
DRUG_PATTERN = re.compile(
    r'\b(' + '|'.join(COMMON_DRUGS) + r'|[A-Z][a-z]{3,15}(?:ol|statin|pril|sartan|mab|nib|xaban|parin|zole|pine|olol|oxin|done|cin))\b',
    re.IGNORECASE
)
DOSE_PATTERN = re.compile(r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|units|iu|ml)\b', re.IGNORECASE)
FREQUENCY_PATTERN = re.compile(
    r'\b(once daily|twice daily|thrice daily|daily|q\.?d\.?|b\.?i\.?d\.?|t\.?i\.?d\.?|q12h|q24h|weekly|as needed|prn)\b',
    re.IGNORECASE
)
ROUTE_PATTERN = re.compile(r'\b(oral|orally|po|p\.o\.|iv|i\.v\.|intravenous|subcutaneous|sc|s\.c\.)\b', re.IGNORECASE)


class MedicalNLPExtractor:
    """
    NLP service providing medical query expansion, intent classification,
    and pharmacological entity extraction.
    """

    @classmethod
    def expand_medical_acronyms(cls, text: str) -> str:
        """
        Expands clinical abbreviations into full terminology to maximize retrieval hit-rate.
        Example: 'first-line DOAC for AF' -> 'first-line Direct Oral Anticoagulant (DOAC) for Atrial Fibrillation (AF)'
        """
        if not text:
            return ""

        words = re.findall(r'\b[A-Za-z0-9\-\/]+\b', text)
        expanded_text = text

        for word in words:
            upper_word = word.upper()
            if upper_word in MEDICAL_ACRONYMS:
                full_term = MEDICAL_ACRONYMS[upper_word]
                # Replace whole word with "Full Term (ACRONYM)"
                pattern = re.compile(r'\b' + re.escape(word) + r'\b')
                expanded_text = pattern.sub(f"{full_term} ({upper_word})", expanded_text, count=1)

        return expanded_text

    @classmethod
    def classify_clinical_intent(cls, query: str) -> str:
        """
        Classifies user clinical intent into:
        - dosing
        - contraindication
        - treatment
        - diagnosis
        - monitoring
        - general
        """
        q = query.lower()

        if any(term in q for term in ["dose", "dosage", "mg", "frequency", "how much", "titrat", "daily", "b.i.d"]):
            return "dosing"
        if any(term in q for term in ["contraindicat", "avoid", "caution", "black box", "adverse", "risk", "harm", "interaction"]):
            return "contraindication"
        if any(term in q for term in ["treatment", "first-line", "therapy", "manage", "recommend", "drug", "prescrib", "anticoagula"]):
            return "treatment"
        if any(term in q for term in ["diagnos", "criteria", "symptom", "score", "cha2ds2", "has-bled", "test", "presentation"]):
            return "diagnosis"
        if any(term in q for term in ["monitor", "inr", "follow-up", "lab", "level", "check", "renal", "crcl"]):
            return "monitoring"

        return "general"

    @classmethod
    def extract_clinical_claims(cls, text: str) -> List[Dict[str, Any]]:
        """
        Extracts structured pharmaceutical claim tuples from text:
        (drug_name, dosage, unit, route, frequency, sentence_snippet)
        """
        if not text:
            return []

        claims: List[Dict[str, Any]] = []
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        for sent in sentences:
            sent_clean = sent.strip()
            if not sent_clean:
                continue

            drug_matches = list(DRUG_PATTERN.finditer(sent_clean))
            if not drug_matches:
                continue

            # Look for dosages in the same sentence
            dose_matches = list(DOSE_PATTERN.finditer(sent_clean))
            freq_match = FREQUENCY_PATTERN.search(sent_clean)
            route_match = ROUTE_PATTERN.search(sent_clean)

            freq_str = freq_match.group(0).lower() if freq_match else ""
            route_str = route_match.group(0).lower() if route_match else ""

            for i, d_match in enumerate(drug_matches):
                drug_name = d_match.group(0).capitalize()
                d_start = d_match.start()

                # Find the closest dosage to this drug mention
                closest_dose = ""
                closest_unit = ""
                min_dist = float('inf')

                for dm in dose_matches:
                    dist = abs(dm.start() - d_start)
                    if dist < min_dist:
                        min_dist = dist
                        closest_dose = dm.group(1)
                        closest_unit = dm.group(2).lower()

                # Deduplicate by drug + dose in same sentence
                exists = any(
                    c["drug_name"].lower() == drug_name.lower() and c["dosage"] == closest_dose
                    for c in claims
                )
                if not exists:
                    claims.append({
                        "drug_name": drug_name,
                        "dosage": closest_dose,
                        "unit": closest_unit,
                        "route": route_str,
                        "frequency": freq_str,
                        "passage": sent_clean
                    })

        return claims

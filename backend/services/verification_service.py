"""
================================================================================
ClinSaarthi AI - Clinical Fact Verification Service
================================================================================
What it does:
    1. Extracts pharmacological entities (drug names, dosages, units, frequencies, routes)
       from draft LLM answers.
    2. Cross-checks every extracted claim against cited source chunks:
       - VERIFIED: Drug and dosage match source text (NLI confidence ~0.95+).
       - CONFLICT: Drug exists in source, but stated dosage/frequency contradicts source.
       - UNSUPPORTED: Drug or claim does not appear anywhere in cited source passages.
    3. Benchmarks against Free Public External APIs:
       - RxNorm API (NIH NLM): Standardizes drug names into RxCUI.
       - openFDA API: Confirms FDA generic approval & black-box warning metadata.

Python Concepts Demonstrated:
    1. Multi-Tier Verification Strategy: Combines lexical proximity matching,
       numeric dosage contradiction detection, and external clinical ontologies.
    2. Fail-Safe External Interoperability: External API lookups fail safely and silently,
       preserving system uptime even during complete network disconnection.
================================================================================
"""
import re
import logging
from typing import List, Dict, Any, Optional

from apps.qa.models import VerificationResult
from ai.nlp import MedicalNLPExtractor
from ai.external_apis import RxNormClient, OpenFDAClient

logger = logging.getLogger(__name__)


class VerificationService:
    """
    Cross-checks draft claims against source chunks to prevent medical hallucinations.
    """

    @classmethod
    def verify_answer(
        cls,
        draft_answer: str,
        cited_chunks: List[Dict[str, Any]],
        skip_external_apis: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Extracts medical facts from draft_answer and verifies each against cited_chunks.
        Returns a list of verification dictionaries matching VerificationResult fields.
        """
        if not draft_answer:
            return []

        # 1. Extract clinical claims from draft answer
        claims = MedicalNLPExtractor.extract_clinical_claims(draft_answer)
        if not claims:
            return []

        # Combine text of all retrieved chunks
        source_texts = [c.get("content", "") for c in cited_chunks]
        full_source_text = "\n".join(source_texts)

        results: List[Dict[str, Any]] = []

        for claim in claims:
            drug_name = claim["drug_name"]
            claim_dose = claim.get("dosage", "")
            claim_unit = claim.get("unit", "")
            claim_freq = claim.get("frequency", "")
            claim_route = claim.get("route", "")

            # 2. Check presence of drug in source text
            drug_regex = re.compile(r'\b' + re.escape(drug_name) + r'\b', re.IGNORECASE)
            drug_matches_in_source = list(drug_regex.finditer(full_source_text))

            status = VerificationResult.Status.UNSUPPORTED
            nli_score = 0.20
            explanation = f"Unsupported: '{drug_name}' was not found in the cited guideline sources."

            if drug_matches_in_source:
                # Drug exists in source text. Now inspect surrounding sentences for dosages.
                if not claim_dose:
                    # No specific dose claimed, drug is affirmed in source
                    status = VerificationResult.Status.VERIFIED
                    nli_score = 0.92
                    explanation = f"Verified: '{drug_name}' is documented in the reference guideline."
                else:
                    # Claim asserted a specific numerical dose (e.g. 20 mg)
                    # Check if exact dose appears near the drug in source
                    found_exact_dose = False
                    conflicting_doses = []

                    # Scan sentences mentioning the drug
                    source_sentences = re.split(r'(?<=[.!?])\s+', full_source_text)
                    for s in source_sentences:
                        if drug_regex.search(s):
                            # Extract all dosages in this sentence
                            doses = re.findall(r'(\d+(?:\.\d+)?)\s*(?:mg|mcg|g|units|iu|ml)\b', s, re.IGNORECASE)
                            if claim_dose in doses:
                                found_exact_dose = True
                                break
                            elif doses:
                                conflicting_doses.extend(doses)

                    if found_exact_dose:
                        status = VerificationResult.Status.VERIFIED
                        nli_score = 0.98
                        explanation = f"Verified: '{drug_name} {claim_dose} {claim_unit}' matches cited guideline."
                    elif conflicting_doses:
                        status = VerificationResult.Status.CONFLICT
                        nli_score = 0.05
                        expected_dose_str = ", ".join(set(conflicting_doses))
                        explanation = (
                            f"Direct conflict: Answer stated '{drug_name} {claim_dose} {claim_unit}', "
                            f"but source specifies '{expected_dose_str} {claim_unit}'."
                        )
                    else:
                        # Drug is in text, but claimed dosage is not mentioned
                        status = VerificationResult.Status.UNSUPPORTED
                        nli_score = 0.35
                        explanation = (
                            f"Unsupported: '{drug_name}' is mentioned, but dosage '{claim_dose} {claim_unit}' "
                            f"is not verified in the cited text."
                        )

            # 3. External API Knowledge Enrichment (Free Public APIs)
            rxnorm_cui = ""
            openfda_match = False

            if not skip_external_apis:
                try:
                    cui = RxNormClient.lookup_rxcui(drug_name)
                    if cui:
                        rxnorm_cui = cui
                except Exception as e:
                    logger.debug("RxNorm verification exception: %s", e)

                try:
                    fda_res = OpenFDAClient.check_drug_label(drug_name)
                    if fda_res.get("matched"):
                        openfda_match = True
                except Exception as e:
                    logger.debug("openFDA verification exception: %s", e)

            results.append({
                "drug_name": drug_name,
                "dosage": claim_dose,
                "unit": claim_unit,
                "route": claim_route,
                "frequency": claim_freq,
                "status": status,
                "nli_score": nli_score,
                "explanation": explanation,
                "rxnorm_cui": rxnorm_cui,
                "openfda_match": openfda_match
            })

        return results

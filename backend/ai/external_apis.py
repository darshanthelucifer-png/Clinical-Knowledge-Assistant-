"""
================================================================================
ClinSaarthi AI - External Public Health APIs (RxNorm & openFDA)
================================================================================
What it does:
    Provides lightweight, zero-key, zero-cost clients for free public medical APIs:
    1. RxNorm API (U.S. National Library of Medicine / NIH)
       - Free REST API: https://rxnav.nlm.nih.gov/REST/
       - Standardizes drug names into RxNorm Concept Unique Identifiers (RxCUI).
       - Validates pharmaceutical spelling and normalized clinical drug concepts.
    2. openFDA API (U.S. Food and Drug Administration)
       - Free REST API: https://api.fda.gov/drug/label.json
       - Verifies FDA-approved generic names, black-box warnings, and contraindications.

Python Concepts Demonstrated:
    1. Caching / Memoization: lru_cache prevents redundant network calls for identical drugs.
    2. Graceful Degradation / Resilience: Uses short timeouts (1.5s) and catch-all exceptions
       so network hiccups or offline mode never crash the clinical pipeline.
    3. Pure Standard Library: Uses urllib.request without requiring external dependencies.
================================================================================
"""
import json
import logging
import urllib.parse
import urllib.request
from functools import lru_cache
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RxNormClient:
    """
    Client for NIH NLM RxNav REST API.
    100% Free, No API Key Required.
    API Docs: https://lhncbc.nlm.nih.gov/RxNav/APIs/RxNormAPIs.html
    """
    BASE_URL = "https://rxnav.nlm.nih.gov/REST"

    @classmethod
    @lru_cache(maxsize=256)
    def lookup_rxcui(cls, drug_name: str) -> Optional[str]:
        """
        Retrieves the RxNorm Concept Unique Identifier (RxCUI) for a drug name.
        Example: 'Rivaroxaban' -> '1114195'
        """
        if not drug_name or len(drug_name.strip()) < 2:
            return None

        clean_name = drug_name.strip().lower()
        encoded = urllib.parse.quote(clean_name)
        url = f"{cls.BASE_URL}/rxcui.json?name={encoded}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ClinSaarthi-AI/1.0 (Clinical-Assistant; Open-Source)"}
            )
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode('utf-8'))
                    id_group = payload.get("idGroup", {})
                    rxnorm_ids = id_group.get("rxnormId", [])
                    if rxnorm_ids:
                        return str(rxnorm_ids[0])
        except Exception as e:
            logger.debug("RxNorm lookup failed for '%s': %s", drug_name, e)

        return None

    @classmethod
    @lru_cache(maxsize=256)
    def get_drug_properties(cls, rxcui: str) -> Dict[str, Any]:
        """
        Retrieves official standardized name and drug type for a given RxCUI.
        """
        if not rxcui:
            return {}

        url = f"{cls.BASE_URL}/rxcui/{rxcui}/properties.json"
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ClinSaarthi-AI/1.0 (Clinical-Assistant; Open-Source)"}
            )
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode('utf-8'))
                    props = payload.get("properties", {})
                    return {
                        "name": props.get("name", ""),
                        "synonym": props.get("synonym", ""),
                        "tty": props.get("tty", "")
                    }
        except Exception as e:
            logger.debug("RxNorm properties lookup failed for rxcui %s: %s", rxcui, e)

        return {}


class OpenFDAClient:
    """
    Client for open.fda.gov Public Drug Labeling API.
    100% Free, No API Key Required (rate limited to 240 requests/min without key).
    API Docs: https://open.fda.gov/apis/drug/label/
    """
    BASE_URL = "https://api.fda.gov/drug/label.json"

    @classmethod
    @lru_cache(maxsize=256)
    def check_drug_label(cls, drug_name: str) -> Dict[str, Any]:
        """
        Queries openFDA to verify FDA approval and extract black box warnings or contraindications.
        """
        if not drug_name or len(drug_name.strip()) < 2:
            return {"matched": False}

        clean_name = drug_name.strip().lower()
        query = f'openfda.generic_name:"{clean_name}"+OR+openfda.brand_name:"{clean_name}"'
        encoded_query = urllib.parse.quote(query, safe='+":')
        url = f"{cls.BASE_URL}?search={encoded_query}&limit=1"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "ClinSaarthi-AI/1.0 (Clinical-Assistant; Open-Source)"}
            )
            with urllib.request.urlopen(req, timeout=2.0) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode('utf-8'))
                    results = payload.get("results", [])
                    if results:
                        label = results[0]
                        boxed_warning = label.get("boxed_warning", [])
                        contraindications = label.get("contraindications", [])
                        return {
                            "matched": True,
                            "generic_name": label.get("openfda", {}).get("generic_name", [drug_name])[0],
                            "brand_name": label.get("openfda", {}).get("brand_name", [""])[0],
                            "has_boxed_warning": bool(boxed_warning),
                            "has_contraindications": bool(contraindications)
                        }
        except Exception as e:
            logger.debug("openFDA lookup failed for '%s': %s", drug_name, e)

        return {"matched": False}

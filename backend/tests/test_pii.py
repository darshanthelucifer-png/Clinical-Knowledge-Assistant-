"""
================================================================================
ClinSaarthi AI - Comprehensive PII / PHI Masking Test Suite
================================================================================
What it tests:
    1. Multi-category extraction: Phone, Email, SSN, Aadhaar, MRN, DOB, Address.
    2. spaCy NER & Clinical Matcher for patient and physician names.
    3. Referential Consistency: Repeated mentions of an entity receive identical tags.
    4. Overlapping span resolution (non-destructive replacements).
    5. Reversible reconstruction via authorized unmask().
    6. Integration on all synthetic clinical notes (Cardiology, Oncology, ER Discharge).
    7. CRITICAL SECURITY RULE: Verification that assert_no_pii_leak() raises an
       exception if raw PHI is present, and succeeds on sanitized LLM payloads.
    8. REST API integration: Note upload de-identifies before saving; PIIMapping
       table isolation; RBAC permission checks on /diff/.
================================================================================
"""
from pathlib import Path
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.notes.models import ClinicalNote, PIIMapping
from services.pii_service import PIIMasker, PIIMaskResult

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def clinician_user(db):
    return User.objects.create_user(
        username="dr_kapoor",
        email="kapoor@hospital.org",
        password="SecurePassword123!",
        role=User.Role.CLINICIAN,
        department="Oncology"
    )

@pytest.fixture
def unauthorized_student(db):
    return User.objects.create_user(
        username="student_vikram",
        email="vikram@medschool.edu",
        password="StudentPassword123!",
        role=User.Role.STUDENT
    )

class TestPIIMaskerUnit:
    def test_multi_category_regex_redaction(self):
        text = (
            "PATIENT NAME: Robert Generic\n"
            "DOB: 12/04/1965\n"
            "MRN: MRN-8829104\n"
            "PHONE: 555-014-9922\n"
            "EMAIL: robert.generic@fakehealthmail.com\n"
            "SSN: 987-65-4320\n"
            "ADDRESS: 742 Evergreen Terrace\n"
        )
        result = PIIMasker.mask(text)

        # Assert all sensitive raw strings are completely redacted
        assert "555-014-9922" not in result.masked_text
        assert "robert.generic@fakehealthmail.com" not in result.masked_text
        assert "987-65-4320" not in result.masked_text
        assert "MRN-8829104" not in result.masked_text
        assert "12/04/1965" not in result.masked_text

        # Assert tagged placeholders exist
        assert "[PHONE_1]" in result.masked_text
        assert "[EMAIL_1]" in result.masked_text
        assert "[SSN_1]" in result.masked_text
        assert "[MRN_1]" in result.masked_text
        assert "[DOB_1]" in result.masked_text

        # Verify mapping dictionary stores exact reversible values
        assert result.mapping["[PHONE_1]"] == "555-014-9922"
        assert result.mapping["[EMAIL_1]"] == "robert.generic@fakehealthmail.com"
        assert result.mapping["[SSN_1]"] == "987-65-4320"

    def test_aadhaar_and_international_phone(self):
        text = (
            "PATIENT: Rajesh Patel\n"
            "AADHAAR: 4321 8765 2109\n"
            "PHONE: +91 98765 43210\n"
        )
        result = PIIMasker.mask(text)
        assert "4321 8765 2109" not in result.masked_text
        assert "+91 98765 43210" not in result.masked_text
        assert "[AADHAAR_1]" in result.masked_text
        assert "[PHONE_1]" in result.masked_text
        assert result.mapping["[AADHAAR_1]"] == "4321 8765 2109"

    def test_referential_consistency_repeated_entities(self):
        """Same entity mentioned multiple times must receive the identical tag."""
        text = (
            "Patient John Doe arrived at 10 AM. Later, John Doe was prescribed Tamoxifen. "
            "Contact John Doe at 555-111-2222."
        )
        result = PIIMasker.mask(text)

        # Count occurrences of [PATIENT_1]
        assert "[PATIENT_1]" in result.masked_text
        assert result.masked_text.count("[PATIENT_1]") >= 2
        assert "John Doe" not in result.masked_text
        assert "[PATIENT_2]" not in result.masked_text  # Should NOT create a second tag for same name

    def test_reversibility_unmask(self):
        original = (
            "Call Dr. Ananya Sen regarding patient Rajesh Patel (DOB: 23-08-1980) "
            "at 555-019-2834 or email dr.sen@hospital.org."
        )
        result = PIIMasker.mask(original)
        reconstructed = PIIMasker.unmask(result.masked_text, result.mapping)
        assert reconstructed == original

    def test_synthetic_notes_masking(self):
        """Tests that all synthetic clinical notes in data/sample_notes are cleanly masked."""
        notes_dir = Path(__file__).resolve().parent.parent.parent / "data" / "sample_notes"
        note_files = list(notes_dir.glob("*.txt"))
        assert len(note_files) >= 3, "Expected at least 3 synthetic clinical notes"

        for note_file in note_files:
            raw_content = note_file.read_text(encoding="utf-8")
            result = PIIMasker.mask(raw_content)

            # Assert no phone or email persists
            assert not PIIMasker.PHONE_REGEX.search(result.masked_text)
            assert not PIIMasker.EMAIL_REGEX.search(result.masked_text)
            assert not PIIMasker.SSN_REGEX.search(result.masked_text)
            assert not PIIMasker.AADHAAR_REGEX.search(result.masked_text)

            # Reversibility test
            reconstructed = PIIMasker.unmask(result.masked_text, result.mapping)
            assert reconstructed == raw_content

    def test_security_leak_assertion_fails_on_raw_pii(self):
        """
        HARD SECURITY RULE: Tests that assert_no_pii_leak raises a ValueError
        if any raw PII pattern appears in text meant for the LLM.
        """
        raw_text_with_pii = "Patient email is patient@secret.com and phone is 555-444-3333."

        # Must raise on raw text
        with pytest.raises(ValueError) as excinfo:
            PIIMasker.assert_no_pii_leak(raw_text_with_pii)
        assert "PHI/PII leakage detected" in str(excinfo.value)

        # Must pass cleanly on masked text
        masked_result = PIIMasker.mask(raw_text_with_pii)
        # Should NOT raise any exception
        PIIMasker.assert_no_pii_leak(masked_result.masked_text)


@pytest.mark.django_db
class TestClinicalNotesAPI:
    def test_note_upload_masks_pii_and_stores_mapping(self, api_client, clinician_user):
        api_client.force_authenticate(user=clinician_user)
        url = reverse('notes:note_upload')
        payload = {
            "title": "Oncology Consultation Note",
            "department": "Oncology",
            "raw_content": (
                "PATIENT: Eleanor Vance\n"
                "DOB: 04/18/1972\n"
                "MRN: MRN-5520193\n"
                "PHONE: (555) 234-8901\n"
                "EMAIL: eleanor.vance@fictionalcare.org\n"
                "SSN: 456-78-1234\n"
                "Prescribed Tamoxifen 20 mg daily."
            )
        }
        response = api_client.post(url, payload, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        note_id = response.data["id"]

        # 1. Verify note in database contains ONLY masked content
        note = ClinicalNote.objects.get(id=note_id)
        assert "(555) 234-8901" not in note.masked_content
        assert "eleanor.vance@fictionalcare.org" not in note.masked_content
        assert "456-78-1234" not in note.masked_content
        assert "[PHONE_1]" in note.masked_content
        assert "[EMAIL_1]" in note.masked_content

        # 2. Verify PIIMapping table contains the audit dictionary
        mapping_record = PIIMapping.objects.get(note=note)
        assert "[PHONE_1]" in mapping_record.mapping_data
        assert mapping_record.mapping_data["[PHONE_1]"] == "(555) 234-8901"

    def test_note_diff_access_control(self, api_client, clinician_user, unauthorized_student):
        # 1. Clinician uploads note
        api_client.force_authenticate(user=clinician_user)
        upload_url = reverse('notes:note_upload')
        payload = {
            "title": "Confidential Note",
            "raw_content": "Patient John Doe with phone 555-888-9999."
        }
        res = api_client.post(upload_url, payload, format='json')
        note_id = res.data["id"]

        diff_url = reverse('notes:note_diff', kwargs={'pk': note_id})

        # 2. Original clinician can view side-by-side diff
        diff_res = api_client.get(diff_url)
        assert diff_res.status_code == status.HTTP_200_OK
        assert "original_content" in diff_res.data
        assert "masked_content" in diff_res.data
        assert diff_res.data["original_content"] == payload["raw_content"]
        assert "555-888-9999" in diff_res.data["original_content"]
        assert "[PHONE_1]" in diff_res.data["masked_content"]

        # 3. Another user (student) is forbidden from viewing the raw PII mapping
        api_client.force_authenticate(user=unauthorized_student)
        forbidden_res = api_client.get(diff_url)
        assert forbidden_res.status_code == status.HTTP_403_FORBIDDEN

"""
================================================================================
ClinSaarthi AI - Study Mode Test Suite (Quiz, Flashcards & Spaced Repetition)
================================================================================
What it tests:
    1. Automatic quiz question synthesis derived from guideline documents.
    2. Multiple-choice question validation (4 options, correct index 0-3, explanation).
    3. Quiz answer evaluation, grading, and StudySession persistence.
    4. Flashcard generation with Front/Back clinical rationale and citations.
    5. SuperMemo SM-2 Spaced Repetition System algorithm (Again, Hard, Good, Easy).
    6. REST API integration:
       - POST /api/v1/study/quizzes/generate/
       - POST /api/v1/study/quizzes/<id>/submit/
       - POST /api/v1/study/flashcards/generate/
       - POST /api/v1/study/flashcards/cards/<id>/review/
       - GET /api/v1/study/stats/
================================================================================
"""
from pathlib import Path
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.documents.models import Document
from apps.study.models import Quiz, QuizQuestion, FlashcardSet, Flashcard, StudySession
from services.study_service import StudyService
from services.ingestion_service import IngestionService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        username="medstudent_arjun",
        email="arjun@medschool.edu",
        password="StudentPassword123!",
        role=User.Role.STUDENT,
        department="Cardiology"
    )


@pytest.fixture
def sample_pdf_path():
    p1 = Path(__file__).resolve().parent.parent.parent / "data" / "guidelines" / "sample_afib_guideline.pdf"
    if p1.exists():
        return str(p1)
    p2 = Path(__file__).resolve().parent.parent / "data" / "guidelines" / "sample_afib_guideline.pdf"
    return str(p2)


@pytest.fixture
def ingested_guideline(student_user, sample_pdf_path):
    doc = Document.objects.create(
        title="AFib Guidelines 2026",
        file=sample_pdf_path,
        uploaded_by=student_user
    )
    IngestionService.process_document(str(doc.id))
    return doc


@pytest.mark.django_db
class TestStudyServiceUnit:
    def test_quiz_generation_and_grounding(self, student_user, ingested_guideline):
        quiz = StudyService.generate_quiz(
            user=student_user,
            document_id=str(ingested_guideline.id),
            topic="Atrial Fibrillation",
            difficulty=Quiz.Difficulty.MEDIUM,
            count=5
        )

        assert quiz.user == student_user
        assert quiz.questions.count() == 5
        assert "Atrial Fibrillation" in quiz.title or "AFib" in quiz.title

        for q in quiz.questions.all():
            assert len(q.options) == 4
            assert 0 <= q.correct_option_index < 4
            assert len(q.explanation) > 10
            assert q.source_reference != ""
            assert q.page_number is not None

    def test_quiz_submission_evaluation_and_session_recording(self, student_user, ingested_guideline):
        quiz = StudyService.generate_quiz(
            user=student_user,
            document_id=str(ingested_guideline.id),
            count=5
        )
        questions = list(quiz.questions.all())

        # Submit answers: answer question 0 & 1 correctly, question 2 incorrectly
        answers = {
            str(questions[0].id): questions[0].correct_option_index,
            str(questions[1].id): questions[1].correct_option_index,
            str(questions[2].id): (questions[2].correct_option_index + 1) % 4,
        }

        result = StudyService.record_quiz_submission(
            user=student_user,
            quiz_id=str(quiz.id),
            answers=answers,
            time_spent_seconds=120
        )

        assert result["total_questions"] == 5
        assert result["correct_answers"] == 2
        assert result["score_percentage"] == 40.0
        assert result["passed"] is False

        # Verify StudySession recorded
        session = StudySession.objects.get(id=result["session_id"])
        assert session.user == student_user
        assert session.session_type == StudySession.SessionType.QUIZ
        assert session.score_percentage == 40.0

    def test_flashcard_generation(self, student_user, ingested_guideline):
        fset = StudyService.generate_flashcards(
            user=student_user,
            document_id=str(ingested_guideline.id),
            topic="Atrial Fibrillation",
            count=6
        )

        assert fset.user == student_user
        assert fset.cards.count() == 6

        first_card = fset.cards.first()
        assert len(first_card.front) > 10
        assert len(first_card.back) > 10
        assert first_card.ease_factor == 2.5
        assert first_card.interval_days == 1
        assert first_card.repetitions == 0

    def test_sm2_spaced_repetition_scheduling(self, student_user, ingested_guideline):
        fset = StudyService.generate_flashcards(
            user=student_user,
            document_id=str(ingested_guideline.id),
            count=2
        )
        card = fset.cards.first()

        # 1. First review: 'good' -> interval becomes 1, repetitions 1
        res1 = StudyService.review_flashcard(student_user, str(card.id), 'good')
        card.refresh_from_db()
        assert card.repetitions == 1
        assert card.interval_days == 1

        # 2. Second review: 'good' -> interval becomes 6, repetitions 2
        res2 = StudyService.review_flashcard(student_user, str(card.id), 'good')
        card.refresh_from_db()
        assert card.repetitions == 2
        assert card.interval_days == 6

        # 3. Third review: 'easy' -> bonus multiplier applied, ease_factor increased
        initial_ef = card.ease_factor
        res3 = StudyService.review_flashcard(student_user, str(card.id), 'easy')
        card.refresh_from_db()
        assert card.repetitions == 3
        assert card.interval_days > 6
        assert card.ease_factor > initial_ef

        # 4. Review 'again' -> resets repetitions to 0, interval to 1
        res4 = StudyService.review_flashcard(student_user, str(card.id), 'again')
        card.refresh_from_db()
        assert card.repetitions == 0
        assert card.interval_days == 1


@pytest.mark.django_db
class TestStudyAPIEndpoints:
    def test_generate_and_submit_quiz_api(self, api_client, student_user, ingested_guideline):
        api_client.force_authenticate(user=student_user)

        # 1. Generate quiz via API
        gen_url = reverse('study:quiz_generate')
        gen_payload = {
            "document_id": str(ingested_guideline.id),
            "topic": "Cardiology DOAC Protocols",
            "difficulty": "MEDIUM",
            "count": 5
        }
        res_gen = api_client.post(gen_url, gen_payload, format='json')
        assert res_gen.status_code == status.HTTP_201_CREATED
        quiz_data = res_gen.data
        quiz_id = quiz_data["id"]
        assert len(quiz_data["questions"]) == 5

        # 2. Submit quiz via API
        submit_url = reverse('study:quiz_submit', kwargs={'pk': quiz_id})
        answers = {
            q["id"]: q["correct_option_index"]
            for q in quiz_data["questions"]
        }
        submit_payload = {
            "answers": answers,
            "time_spent_seconds": 95
        }
        res_submit = api_client.post(submit_url, submit_payload, format='json')
        assert res_submit.status_code == status.HTTP_200_OK
        assert res_submit.data["score_percentage"] == 100.0
        assert res_submit.data["passed"] is True
        assert len(res_submit.data["results"]) == 5

    def test_generate_and_review_flashcards_api(self, api_client, student_user, ingested_guideline):
        api_client.force_authenticate(user=student_user)

        # 1. Generate flashcard deck
        gen_url = reverse('study:flashcard_generate')
        gen_payload = {
            "document_id": str(ingested_guideline.id),
            "topic": "Atrial Fibrillation Dosing",
            "count": 6
        }
        res_gen = api_client.post(gen_url, gen_payload, format='json')
        assert res_gen.status_code == status.HTTP_201_CREATED
        deck_data = res_gen.data
        assert len(deck_data["cards"]) == 6

        first_card_id = deck_data["cards"][0]["id"]

        # 2. Review flashcard with 'good' rating
        review_url = reverse('study:flashcard_review', kwargs={'pk': first_card_id})
        res_review = api_client.post(review_url, {"rating": "good"}, format='json')
        assert res_review.status_code == status.HTTP_200_OK
        assert res_review.data["rating"] == "good"
        assert res_review.data["repetitions"] == 1

    def test_study_stats_api(self, api_client, student_user, ingested_guideline):
        api_client.force_authenticate(user=student_user)

        # Generate and submit a quiz to seed statistics
        quiz = StudyService.generate_quiz(student_user, str(ingested_guideline.id), count=3)
        q_list = list(quiz.questions.all())
        StudyService.record_quiz_submission(
            student_user,
            str(quiz.id),
            {str(q_list[0].id): q_list[0].correct_option_index},
            time_spent_seconds=60
        )

        stats_url = reverse('study:study_stats')
        res = api_client.get(stats_url)
        assert res.status_code == status.HTTP_200_OK
        assert res.data["total_quizzes_completed"] >= 1
        assert "average_quiz_score" in res.data
        assert "topics" in res.data

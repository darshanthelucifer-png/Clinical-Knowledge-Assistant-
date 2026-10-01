"""
================================================================================
ClinSaarthi AI - Study Mode Views
================================================================================
What it does:
    Provides RESTful endpoints for:
    - Synthesizing quizzes and flashcard sets grounded in guidelines.
    - Answering quizzes and receiving instant rationales + citation page links.
    - SuperMemo SM-2 spaced repetition self-rating.
    - Fetching study performance analytics.
================================================================================
"""
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Quiz, FlashcardSet, Flashcard, StudySession
from .serializers import (
    QuizSerializer,
    QuizGenerateInputSerializer,
    QuizSubmitInputSerializer,
    FlashcardSetSerializer,
    FlashcardGenerateInputSerializer,
    FlashcardReviewInputSerializer,
    StudySessionSerializer,
)
from services.study_service import StudyService


class QuizListView(generics.ListCreateAPIView):
    """
    GET /api/v1/study/quizzes/
    Lists quizzes created for or by the user.
    """
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class QuizDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/v1/study/quizzes/<id>/
    Retrieves full quiz with questions.
    """
    serializer_class = QuizSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)


class QuizGenerateView(APIView):
    """
    POST /api/v1/study/quizzes/generate/
    Generates a new multiple-choice quiz grounded in guideline chunks.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'quiz'

    def post(self, request, *args, **kwargs):
        serializer = QuizGenerateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document_id = serializer.validated_data.get('document_id')
        topic = serializer.validated_data.get('topic', 'Atrial Fibrillation')
        difficulty = serializer.validated_data.get('difficulty', Quiz.Difficulty.MEDIUM)
        count = serializer.validated_data.get('count', 5)

        quiz = StudyService.generate_quiz(
            user=request.user,
            document_id=str(document_id) if document_id else None,
            topic=topic,
            difficulty=difficulty,
            count=count
        )

        return Response(QuizSerializer(quiz).data, status=status.HTTP_201_CREATED)


class QuizSubmitView(APIView):
    """
    POST /api/v1/study/quizzes/<id>/submit/
    Submits user answers, calculates score, and records study session.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        serializer = QuizSubmitInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        answers = serializer.validated_data['answers']
        time_spent = serializer.validated_data.get('time_spent_seconds', 0)

        try:
            Quiz.objects.get(id=pk, user=request.user)
        except Quiz.DoesNotExist:
            return Response({"error": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

        result = StudyService.record_quiz_submission(
            user=request.user,
            quiz_id=str(pk),
            answers=answers,
            time_spent_seconds=time_spent
        )

        return Response(result, status=status.HTTP_200_OK)


class FlashcardSetListView(generics.ListCreateAPIView):
    """
    GET /api/v1/study/flashcards/
    Lists flashcard decks for the user.
    """
    serializer_class = FlashcardSetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FlashcardSet.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FlashcardSetDetailView(generics.RetrieveDestroyAPIView):
    """
    GET /api/v1/study/flashcards/<id>/
    Retrieves full flashcard deck with SRS metrics.
    """
    serializer_class = FlashcardSetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FlashcardSet.objects.filter(user=self.request.user)


class FlashcardGenerateView(APIView):
    """
    POST /api/v1/study/flashcards/generate/
    Synthesizes clinical flashcards with front/back rationale and SM-2 scheduling.
    """
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = 'quiz'

    def post(self, request, *args, **kwargs):
        serializer = FlashcardGenerateInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        document_id = serializer.validated_data.get('document_id')
        topic = serializer.validated_data.get('topic', 'Atrial Fibrillation')
        count = serializer.validated_data.get('count', 6)

        fset = StudyService.generate_flashcards(
            user=request.user,
            document_id=str(document_id) if document_id else None,
            topic=topic,
            count=count
        )

        return Response(FlashcardSetSerializer(fset).data, status=status.HTTP_201_CREATED)


class FlashcardReviewView(APIView):
    """
    POST /api/v1/study/flashcards/cards/<id>/review/
    Applies SuperMemo SM-2 self-rating (again, hard, good, easy) to an individual card.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk, *args, **kwargs):
        serializer = FlashcardReviewInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        rating = serializer.validated_data['rating']

        try:
            Flashcard.objects.get(id=pk, flashcard_set__user=request.user)
        except Flashcard.DoesNotExist:
            return Response({"error": "Flashcard not found."}, status=status.HTTP_404_NOT_FOUND)

        result = StudyService.review_flashcard(
            user=request.user,
            flashcard_id=str(pk),
            rating=rating
        )

        return Response(result, status=status.HTTP_200_OK)


class StudyStatsView(APIView):
    """
    GET /api/v1/study/stats/
    Returns aggregate study metrics (quizzes, avg score, flashcards reviewed, topics).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        stats = StudyService.get_user_stats(request.user)
        return Response(stats, status=status.HTTP_200_OK)

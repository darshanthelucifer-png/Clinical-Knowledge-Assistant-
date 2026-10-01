"""
================================================================================
ClinSaarthi AI - Study Mode URL Routing
================================================================================
"""
from django.urls import path
from .views import (
    QuizListView,
    QuizDetailView,
    QuizGenerateView,
    QuizSubmitView,
    FlashcardSetListView,
    FlashcardSetDetailView,
    FlashcardGenerateView,
    FlashcardReviewView,
    StudyStatsView,
)

app_name = 'study'

urlpatterns = [
    # Quizzes
    path('quizzes/', QuizListView.as_view(), name='quiz_list'),
    path('quizzes/generate/', QuizGenerateView.as_view(), name='quiz_generate'),
    path('quizzes/<uuid:pk>/', QuizDetailView.as_view(), name='quiz_detail'),
    path('quizzes/<uuid:pk>/submit/', QuizSubmitView.as_view(), name='quiz_submit'),

    # Flashcards
    path('flashcards/', FlashcardSetListView.as_view(), name='flashcard_list'),
    path('flashcards/generate/', FlashcardGenerateView.as_view(), name='flashcard_generate'),
    path('flashcards/<uuid:pk>/', FlashcardSetDetailView.as_view(), name='flashcard_detail'),
    path('flashcards/cards/<uuid:pk>/review/', FlashcardReviewView.as_view(), name='flashcard_review'),

    # Analytics
    path('stats/', StudyStatsView.as_view(), name='study_stats'),
]

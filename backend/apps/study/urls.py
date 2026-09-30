"""
URL Routing for Study Mode
"""
from django.urls import path
from .views import (
    QuizListView,
    QuizDetailView,
    FlashcardSetListView,
    FlashcardSetDetailView,
)

app_name = 'study'

urlpatterns = [
    path('quizzes/', QuizListView.as_view(), name='quiz_list'),
    path('quizzes/<uuid:pk>/', QuizDetailView.as_view(), name='quiz_detail'),
    path('flashcards/', FlashcardSetListView.as_view(), name='flashcard_list'),
    path('flashcards/<uuid:pk>/', FlashcardSetDetailView.as_view(), name='flashcard_detail'),
]

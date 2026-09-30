"""
================================================================================
ClinSaarthi AI - Study Mode Models (Quiz & Flashcards)
================================================================================
What it does:
    Stores guideline-grounded multiple-choice quizzes and medical flashcards
    generated automatically from parsed clinical documents.

Python Concepts Demonstrated:
    1. Hierarchical Data Modeling: Quiz -> QuizQuestion, FlashcardSet -> Flashcard.
    2. JSON Serialization: Storing dynamic multiple choice options in JSONField.
================================================================================
"""
import uuid
from django.db import models
from django.conf import settings
from apps.documents.models import Document

class Quiz(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'EASY', 'Basic Terminology & Concepts'
        MEDIUM = 'MEDIUM', 'Clinical Scenarios & Guidelines'
        HARD = 'HARD', 'Complex Pharmacology & Differential Diagnosis'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quizzes')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='quizzes')
    title = models.CharField(max_length=255)
    topic = models.CharField(max_length=150, blank=True)
    difficulty = models.CharField(max_length=20, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.title} ({self.difficulty})"


class QuizQuestion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    # List of string options, e.g. ["Aspirin", "Clopidogrel", "Warfarin", "Heparin"]
    options = models.JSONField(default=list)
    correct_option_index = models.PositiveSmallIntegerField(help_text="0-indexed pointer to correct option")
    explanation = models.TextField(blank=True, help_text="Clinical justification grounded in source text")
    source_reference = models.CharField(max_length=255, blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)

    def __str__(self) -> str:
        return f"Q: {self.question_text[:50]}..."


class FlashcardSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flashcard_sets')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='flashcard_sets')
    title = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.title


class Flashcard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='cards')
    front = models.TextField(help_text="Clinical question, symptom cluster, or drug name")
    back = models.TextField(help_text="Mechanism, guideline recommendation, dosage, or contraindication")
    key_concept = models.CharField(max_length=150, blank=True)
    source_reference = models.CharField(max_length=255, blank=True)

    def __str__(self) -> str:
        return f"Card: {self.front[:40]}..."

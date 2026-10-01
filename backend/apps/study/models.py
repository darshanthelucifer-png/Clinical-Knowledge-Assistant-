"""
================================================================================
ClinSaarthi AI - Study Mode Models (Quiz, Flashcards & Spaced Repetition)
================================================================================
What it does:
    Stores guideline-grounded multiple-choice quizzes, medical flashcards with
    SuperMemo SM-2 Spaced Repetition System (SRS) tracking, and study session
    performance analytics for medical students and clinicians.

Python Concepts Demonstrated:
    1. Hierarchical Relational Modeling:
       Quiz -> QuizQuestion, FlashcardSet -> Flashcard, User -> StudySession.
    2. Dynamic Serialization: Storing dynamic multiple choice options in JSONField.
    3. Spaced Repetition Scheduling: SM-2 interval and ease factor algorithms.
================================================================================
"""
import uuid
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.utils import timezone
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

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return f"Q: {self.question_text[:50]}..."


class FlashcardSet(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='flashcard_sets')
    document = models.ForeignKey(Document, on_delete=models.SET_NULL, null=True, blank=True, related_name='flashcard_sets')
    title = models.CharField(max_length=255)
    topic = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title


class Flashcard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.CASCADE, related_name='cards')
    front = models.TextField(help_text="Clinical question, symptom cluster, or drug name")
    back = models.TextField(help_text="Mechanism, guideline recommendation, dosage, or contraindication")
    key_concept = models.CharField(max_length=150, blank=True)
    source_reference = models.CharField(max_length=255, blank=True)
    page_number = models.PositiveIntegerField(null=True, blank=True)

    # SuperMemo SM-2 Spaced Repetition Fields
    ease_factor = models.FloatField(default=2.5, help_text="Difficulty multiplier (minimum 1.3)")
    interval_days = models.PositiveIntegerField(default=1, help_text="Days until next review")
    repetitions = models.PositiveIntegerField(default=0, help_text="Consecutive successful recalls")
    last_reviewed = models.DateTimeField(null=True, blank=True)
    next_review = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self) -> str:
        return f"Card: {self.front[:40]}..."

    def apply_srs_rating(self, rating: str) -> None:
        """
        SuperMemo SM-2 Spaced Repetition System calculation.
        Ratings:
            - 'again': Failed recall (quality=1) -> reset reps, interval=1
            - 'hard': Difficult recall (quality=2) -> interval=max(1, int(interval * 1.2))
            - 'good': Successful recall (quality=3) -> standard SM-2 scaling
            - 'easy': Effortless recall (quality=4) -> bonus interval and ease factor boost
        """
        now = timezone.now()
        self.last_reviewed = now

        rating = rating.lower().strip()
        if rating == 'again':
            self.repetitions = 0
            self.interval_days = 1
            # Slightly lower ease factor
            self.ease_factor = max(1.3, self.ease_factor - 0.2)
        elif rating == 'hard':
            self.repetitions += 1
            self.interval_days = max(1, int(self.interval_days * 1.2))
            self.ease_factor = max(1.3, self.ease_factor - 0.15)
        elif rating == 'good':
            self.repetitions += 1
            if self.repetitions == 1:
                self.interval_days = 1
            elif self.repetitions == 2:
                self.interval_days = 6
            else:
                self.interval_days = max(1, int(self.interval_days * self.ease_factor))
        elif rating == 'easy':
            self.repetitions += 1
            if self.repetitions == 1:
                self.interval_days = 3
            elif self.repetitions == 2:
                self.interval_days = 10
            else:
                self.interval_days = max(1, int(self.interval_days * self.ease_factor * 1.3))
            self.ease_factor += 0.15

        self.next_review = now + timedelta(days=self.interval_days)
        self.save()


class StudySession(models.Model):
    class SessionType(models.TextChoices):
        QUIZ = 'QUIZ', 'Multiple Choice Quiz'
        FLASHCARD = 'FLASHCARD', 'Flashcard SRS Review'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_sessions')
    session_type = models.CharField(max_length=20, choices=SessionType.choices, default=SessionType.QUIZ)
    quiz = models.ForeignKey(Quiz, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    flashcard_set = models.ForeignKey(FlashcardSet, on_delete=models.SET_NULL, null=True, blank=True, related_name='sessions')
    total_items = models.PositiveIntegerField(default=0)
    correct_items = models.PositiveIntegerField(default=0)
    score_percentage = models.FloatField(default=0.0)
    topic = models.CharField(max_length=150, blank=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.user.username} - {self.session_type} ({self.score_percentage:.1f}%)"

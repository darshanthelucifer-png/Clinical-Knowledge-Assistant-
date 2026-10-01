"""
================================================================================
ClinSaarthi AI - Study Mode Serializers
================================================================================
"""
from rest_framework import serializers
from .models import Quiz, QuizQuestion, FlashcardSet, Flashcard, StudySession


class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = [
            'id', 'question_text', 'options', 'correct_option_index',
            'explanation', 'source_reference', 'page_number'
        ]


class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = Quiz
        fields = [
            'id', 'title', 'topic', 'difficulty',
            'questions_count', 'questions', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class QuizGenerateInputSerializer(serializers.Serializer):
    document_id = serializers.UUIDField(required=False, allow_null=True)
    topic = serializers.CharField(max_length=150, default="Atrial Fibrillation")
    difficulty = serializers.ChoiceField(choices=Quiz.Difficulty.choices, default=Quiz.Difficulty.MEDIUM)
    count = serializers.IntegerField(default=5, min_value=1, max_value=20)


class QuizSubmitInputSerializer(serializers.Serializer):
    answers = serializers.DictField(
        child=serializers.IntegerField(),
        help_text="Dictionary mapping question_id -> selected_option_index (0-3)"
    )
    time_spent_seconds = serializers.IntegerField(default=0, min_value=0)


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = [
            'id', 'front', 'back', 'key_concept', 'source_reference',
            'page_number', 'ease_factor', 'interval_days', 'repetitions',
            'last_reviewed', 'next_review'
        ]
        read_only_fields = ['id', 'ease_factor', 'interval_days', 'repetitions', 'last_reviewed', 'next_review']


class FlashcardSetSerializer(serializers.ModelSerializer):
    cards = FlashcardSerializer(many=True, read_only=True)
    cards_count = serializers.IntegerField(source='cards.count', read_only=True)

    class Meta:
        model = FlashcardSet
        fields = ['id', 'title', 'topic', 'cards_count', 'cards', 'created_at']
        read_only_fields = ['id', 'created_at']


class FlashcardGenerateInputSerializer(serializers.Serializer):
    document_id = serializers.UUIDField(required=False, allow_null=True)
    topic = serializers.CharField(max_length=150, default="Atrial Fibrillation")
    count = serializers.IntegerField(default=6, min_value=1, max_value=30)


class FlashcardReviewInputSerializer(serializers.Serializer):
    rating = serializers.ChoiceField(
        choices=['again', 'hard', 'good', 'easy'],
        help_text="Spaced repetition rating: again (<1d), hard (1.2x), good (SM-2 standard), easy (bonus multiplier)"
    )


class StudySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySession
        fields = [
            'id', 'session_type', 'total_items', 'correct_items',
            'score_percentage', 'topic', 'time_spent_seconds', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

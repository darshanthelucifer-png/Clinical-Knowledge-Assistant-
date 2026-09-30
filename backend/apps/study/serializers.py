"""
Serializers for Study Mode (Quizzes & Flashcards)
"""
from rest_framework import serializers
from .models import Quiz, QuizQuestion, FlashcardSet, Flashcard

class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'question_text', 'options', 'correct_option_index', 'explanation', 'source_reference', 'page_number']

class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)
    questions_count = serializers.IntegerField(source='questions.count', read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'topic', 'difficulty', 'questions_count', 'questions', 'created_at']
        read_only_fields = ['id', 'created_at']

class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ['id', 'front', 'back', 'key_concept', 'source_reference']

class FlashcardSetSerializer(serializers.ModelSerializer):
    cards = FlashcardSerializer(many=True, read_only=True)
    cards_count = serializers.IntegerField(source='cards.count', read_only=True)

    class Meta:
        model = FlashcardSet
        fields = ['id', 'title', 'cards_count', 'cards', 'created_at']
        read_only_fields = ['id', 'created_at']

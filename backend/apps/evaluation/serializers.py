"""
Serializers for RAG Evaluation & Dashboard
"""
from rest_framework import serializers
from .models import GoldenQA, EvalRun

class GoldenQASerializer(serializers.ModelSerializer):
    class Meta:
        model = GoldenQA
        fields = '__all__'

class EvalRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvalRun
        fields = '__all__'

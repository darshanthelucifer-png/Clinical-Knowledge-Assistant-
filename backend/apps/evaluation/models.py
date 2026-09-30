"""
================================================================================
ClinSaarthi AI - RAG Evaluation Models
================================================================================
What it does:
    Stores gold-standard medical QA benchmark pairs and historical evaluation
    run metrics (hit-rate@5, faithfulness, citation precision) for tracking
    retrieval and generation quality over time.

Python Concepts Demonstrated:
    1. Float Fields with Statistical Constraints: Precision scoring (0.0 to 1.0).
    2. Audit Trail Patterns: Tracking configuration changes across benchmark runs.
================================================================================
"""
import uuid
from django.db import models

class GoldenQA(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.TextField()
    expected_answer = models.TextField()
    expected_document = models.CharField(max_length=255)
    expected_page = models.PositiveIntegerField()
    expected_drugs = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=100, default='Pharmacology')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Golden QA: {self.question[:50]}..."


class EvalRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    llm_model = models.CharField(max_length=120)
    embedding_model = models.CharField(max_length=120)
    reranker_model = models.CharField(max_length=120)
    total_samples = models.PositiveIntegerField(default=0)
    hit_rate_at_5 = models.FloatField(help_text="Retrieval hit-rate @ top 5 chunks")
    faithfulness_score = models.FloatField(help_text="NLI entailed claims / total claims")
    citation_accuracy = models.FloatField(help_text="Citations pointing to valid source pages")
    execution_time_seconds = models.FloatField(default=0.0)
    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self) -> str:
        return f"EvalRun {self.timestamp.strftime('%Y-%m-%d %H:%M')} (HitRate: {self.hit_rate_at_5:.2f})"

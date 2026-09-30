"""
Evaluation Views
API for retrieving evaluation dashboard metrics and golden Q&A sets.
"""
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import GoldenQA, EvalRun
from .serializers import GoldenQASerializer, EvalRunSerializer
from services.evaluation_service import EvaluationService

class GoldenQAListView(generics.ListCreateAPIView):
    queryset = GoldenQA.objects.all()
    serializer_class = GoldenQASerializer
    permission_classes = [permissions.IsAuthenticated]

class EvalRunListView(generics.ListAPIView):
    queryset = EvalRun.objects.all().order_by('-timestamp')
    serializer_class = EvalRunSerializer
    permission_classes = [permissions.IsAuthenticated]

class EvalRunDetailView(generics.RetrieveAPIView):
    queryset = EvalRun.objects.all()
    serializer_class = EvalRunSerializer
    permission_classes = [permissions.IsAuthenticated]

class BenchmarkExecuteView(APIView):
    """
    POST /api/v1/evaluation/benchmark/
    Executes benchmark run over the golden QA dataset, records metrics,
    and returns before/after comparisons.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        sample_size = request.data.get('sample_size', None)
        if sample_size is not None:
            try:
                sample_size = int(sample_size)
            except ValueError:
                sample_size = None

        summary = EvaluationService.run_benchmark(sample_size=sample_size)
        return Response({
            "run_id": summary.run_id,
            "timestamp": summary.timestamp,
            "total_samples": summary.total_samples,
            "hit_rate_at_5": summary.hit_rate_at_5,
            "faithfulness_score": summary.faithfulness_score,
            "citation_accuracy": summary.citation_accuracy,
            "execution_time_seconds": summary.execution_time_seconds,
            "delta_hit_rate": summary.delta_hit_rate,
            "delta_faithfulness": summary.delta_faithfulness,
            "delta_citation_accuracy": summary.delta_citation_accuracy,
            "details": summary.details
        }, status=status.HTTP_201_CREATED)

class EvaluationSummaryView(APIView):
    """
    GET /api/v1/evaluation/summary/
    Returns high-level metric cards for the evaluation dashboard.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        latest = EvalRun.objects.first()
        total_runs = EvalRun.objects.count()
        golden_count = GoldenQA.objects.count()

        if not latest:
            return Response({
                "has_runs": False,
                "golden_qa_count": golden_count,
                "total_runs": 0,
                "latest_metrics": None
            })

        return Response({
            "has_runs": True,
            "golden_qa_count": golden_count,
            "total_runs": total_runs,
            "latest_metrics": {
                "id": str(latest.id),
                "timestamp": latest.timestamp.isoformat(),
                "hit_rate_at_5": latest.hit_rate_at_5,
                "faithfulness_score": latest.faithfulness_score,
                "citation_accuracy": latest.citation_accuracy,
                "execution_time_seconds": latest.execution_time_seconds,
                "llm_model": latest.llm_model,
                "embedding_model": latest.embedding_model,
                "reranker_model": latest.reranker_model,
                "deltas": {
                    "hit_rate": latest.details.get("delta_hit_rate", 0.0),
                    "faithfulness": latest.details.get("delta_faithfulness", 0.0),
                    "citation_accuracy": latest.details.get("delta_citation_accuracy", 0.0)
                }
            }
        })

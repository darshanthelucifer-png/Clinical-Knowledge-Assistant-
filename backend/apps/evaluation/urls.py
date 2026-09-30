"""
URL Routing for Evaluation Harness
"""
from django.urls import path
from .views import (
    GoldenQAListView,
    EvalRunListView,
    EvalRunDetailView,
    BenchmarkExecuteView,
    EvaluationSummaryView,
)

app_name = 'evaluation'

urlpatterns = [
    path('golden-qa/', GoldenQAListView.as_view(), name='golden_qa_list'),
    path('runs/', EvalRunListView.as_view(), name='eval_run_list'),
    path('runs/<uuid:pk>/', EvalRunDetailView.as_view(), name='eval_run_detail'),
    path('benchmark/', BenchmarkExecuteView.as_view(), name='benchmark_execute'),
    path('summary/', EvaluationSummaryView.as_view(), name='evaluation_summary'),
]

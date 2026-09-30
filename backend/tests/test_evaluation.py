"""
================================================================================
ClinSaarthi AI - Evaluation Harness & Dashboard Tests
================================================================================
What it tests:
    1. Golden Q&A benchmark template integrity (50 curated medical QA pairs).
    2. Quantitative metrics computation: Hit-rate@5, Faithfulness, Citation accuracy.
    3. Before / After delta tracking across consecutive benchmark runs.
    4. Evaluation REST API: /runs/, /summary/, and /benchmark/ endpoints.
================================================================================
"""
from pathlib import Path
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.evaluation.models import GoldenQA, EvalRun
from services.evaluation_service import EvaluationService

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="eval_admin",
        email="admin@clinsaarthi.ai",
        password="AdminPassword123!",
        role=User.Role.ADMIN
    )

class TestGoldenQADataset:
    def test_golden_qa_contains_50_curated_pairs(self):
        pairs = EvaluationService.load_golden_pairs()
        assert len(pairs) == 50, f"Expected 50 golden QA pairs, found {len(pairs)}"

        # Validate structure of each benchmark pair
        for p in pairs:
            assert "id" in p
            assert "question" in p and len(p["question"]) > 10
            assert "expected_answer" in p and len(p["expected_answer"]) > 10
            assert "expected_document" in p
            assert "expected_page" in p and isinstance(p["expected_page"], int)
            assert "expected_drugs" in p and isinstance(p["expected_drugs"], list)
            assert "category" in p
            assert "difficulty" in p

    def test_nli_entailment_logic(self):
        context = "Apixaban 5 mg twice daily is recommended for stroke prevention in non-valvular AF."
        claim_entailed = "Apixaban 5 mg is administered twice daily."
        claim_unsupported = "Warfarin 10 mg is administered for lung cancer."

        is_entailed, conf1 = EvaluationService.check_nli_entailment(claim_entailed, context)
        assert is_entailed is True
        assert conf1 >= 0.70

        is_not_entailed, conf2 = EvaluationService.check_nli_entailment(claim_unsupported, context)
        assert is_not_entailed is False
        assert conf2 < 0.70

@pytest.mark.django_db
class TestEvaluationService:
    def test_seed_golden_qa_table(self):
        count = EvaluationService.seed_golden_qa_table()
        assert count == 50
        assert GoldenQA.objects.count() == 50

    def test_run_benchmark_and_delta_tracking(self):
        # First Run
        run1 = EvaluationService.run_benchmark(sample_size=10)
        assert run1.total_samples == 10
        assert 0.0 <= run1.hit_rate_at_5 <= 1.0
        assert 0.0 <= run1.faithfulness_score <= 1.0
        assert 0.0 <= run1.citation_accuracy <= 1.0
        assert run1.delta_hit_rate == 0.0  # Initial run has 0.0 delta

        # Second Run (calculates delta vs Run 1)
        run2 = EvaluationService.run_benchmark(sample_size=10)
        assert EvalRun.objects.count() >= 2
        # Delta exists as a float
        assert isinstance(run2.delta_hit_rate, float)
        assert isinstance(run2.delta_faithfulness, float)

@pytest.mark.django_db
class TestEvaluationDashboardAPI:
    def test_evaluation_summary_and_runs_api(self, api_client, admin_user):
        api_client.force_authenticate(user=admin_user)

        # 1. Trigger benchmark run via API
        bench_url = reverse('evaluation:benchmark_execute')
        response = api_client.post(bench_url, {"sample_size": 5}, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert "hit_rate_at_5" in response.data
        assert "faithfulness_score" in response.data
        assert "citation_accuracy" in response.data

        # 2. Get dashboard summary
        summary_url = reverse('evaluation:evaluation_summary')
        sum_res = api_client.get(summary_url)
        assert sum_res.status_code == status.HTTP_200_OK
        assert sum_res.data["has_runs"] is True
        assert sum_res.data["latest_metrics"] is not None
        assert "hit_rate_at_5" in sum_res.data["latest_metrics"]
        assert "deltas" in sum_res.data["latest_metrics"]

        # 3. List historical runs
        runs_url = reverse('evaluation:eval_run_list')
        runs_res = api_client.get(runs_url)
        assert runs_res.status_code == status.HTTP_200_OK
        assert len(runs_res.data.get("results", runs_res.data)) >= 1

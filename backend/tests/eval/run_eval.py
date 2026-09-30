"""
================================================================================
ClinSaarthi AI - Automated RAG Evaluation Benchmark CLI
================================================================================
What it does:
    CLI utility executing quantitative evaluation across 50 Golden Medical Q&A pairs.
    Outputs:
    - Retrieval Hit-Rate@5
    - Answer Faithfulness (NLI Entailment)
    - Citation Precision
    - Execution Latency & Before/After Deltas
================================================================================
"""
import os
import sys
from pathlib import Path
import django

# Setup Django environment
backend_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(backend_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from services.evaluation_service import EvaluationService
from apps.documents.models import Document
from services.ingestion_service import IngestionService

def main():
    print("=" * 72)
    print(" CLINSAARTHI AI - RAG EVALUATION BENCHMARK (50 GOLDEN PAIRS)")
    print("=" * 72)

    # 1. Ensure guideline PDF is ingested
    doc_count = Document.objects.count()
    if doc_count == 0:
        pdf_path = backend_dir.parent / "data" / "guidelines" / "sample_afib_guideline.pdf"
        if pdf_path.exists():
            print(f"[*] Ingesting sample guideline: {pdf_path.name}...")
            doc = Document.objects.create(
                title="AHA Atrial Fibrillation Guideline 2026",
                file=str(pdf_path),
                author_or_source="AHA/ACC/HRS"
            )
            IngestionService.process_document(str(doc.id))
            print(f"[*] Successfully ingested {doc.chunks.count()} chunks into ChromaDB.")

    # 2. Seed Golden QA table
    seeded = EvaluationService.seed_golden_qa_table()
    print(f"[*] Golden Q&A Benchmark dataset loaded: {seeded} pairs.")

    # 3. Execute benchmark
    print("[*] Running hybrid retrieval, NLI faithfulness & citation precision checks...")
    summary = EvaluationService.run_benchmark()

    # 4. Display formatted results
    print("\n" + "=" * 72)
    print(" EVALUATION METRICS REPORT")
    print("=" * 72)
    print(f" Total Samples Evaluated    : {summary.total_samples}")
    print(f" Execution Time             : {summary.execution_time_seconds} s")
    print("-" * 72)
    print(f" Retrieval Hit-Rate @ 5     : {summary.hit_rate_at_5 * 100:.2f}% (Delta: {summary.delta_hit_rate:+0.2%})")
    print(f" Answer Faithfulness (NLI)  : {summary.faithfulness_score * 100:.2f}% (Delta: {summary.delta_faithfulness:+0.2%})")
    print(f" Citation Accuracy          : {summary.citation_accuracy * 100:.2f}% (Delta: {summary.delta_citation_accuracy:+0.2%})")
    print("=" * 72)
    print("[OK] Benchmark successfully recorded in database (EvalRun ID: " + summary.run_id + ")")
    print("=" * 72)

if __name__ == "__main__":
    main()

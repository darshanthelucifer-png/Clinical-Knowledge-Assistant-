# ClinSaarthi AI - RAG Evaluation Framework

## Evaluation Metrics
1. **Retrieval Hit-Rate@5**: Percentage of queries where the true ground-truth guideline chunk was present in the top 5 reranked candidates.
2. **Answer Faithfulness (NLI)**: Ratio of atomic factual claims in the generated response that are logically entailed by the retrieved source chunks.
3. **Citation Precision**: Proportion of inline citations `[n]` where the cited passage actually contains the asserted medical fact.
4. **Drug Safety / Dosage Precision**: Percentage of drug names, dosages, units, and frequencies verified without conflicts.

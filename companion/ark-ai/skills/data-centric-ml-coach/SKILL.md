---
name: data-centric-ml-coach
description: Improve machine-learning and LLM systems by diagnosing and repairing data, labels, evaluation sets, and feedback loops. Use for dataset quality, annotation, error analysis, RAG evaluation, monitoring, distribution shift, or human-in-the-loop ML planning.
---

# Data-Centric ML Coach

1. Define the production decision, unit of analysis, failure cost, and representative evaluation slices.
2. Establish a reproducible baseline and freeze a leakage-safe test set.
3. Build an error taxonomy and rank clusters by frequency and impact.
4. Audit label definitions, ambiguity, agreement, duplicates, contamination, missingness, imbalance, and train/serve skew.
5. Choose the smallest data intervention: relabel, clarify, collect a slice, augment carefully, rebalance, or improve retrieval.
6. Re-run the same global and sliced evaluation, with uncertainty where feasible.
7. Design monitoring and a human feedback loop with retraining triggers.

For RAG, evaluate retrieval and answer quality separately. Calibrate LLM judges against human labels. Based on Data-Centric Deep Learning and Microsoft AI-Edu.

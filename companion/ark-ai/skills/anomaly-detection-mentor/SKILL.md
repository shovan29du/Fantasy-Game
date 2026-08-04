---
name: anomaly-detection-mentor
description: Guide development and evaluation of visual anomaly-detection systems, especially teacher-student networks. Use for defect detection, MVTec-style datasets, anomaly maps, model distillation, thresholding, evaluation, or false-positive diagnosis.
---

# Anomaly Detection Mentor

1. Clarify normal and anomalous data, defect types, resolution, labels, latency, and error costs.
2. Split by object, batch, site, or time to prevent duplicate and production leakage.
3. Establish simple baselines before a teacher-student model.
4. Freeze a pretrained teacher, train the student on normal samples to match multi-scale features, and calculate feature-discrepancy maps.
5. Normalize and combine maps; choose image- and pixel-level thresholds using validation data only.
6. Evaluate AUROC plus threshold precision/recall, localization metrics when masks exist, and results by defect type.
7. Inspect errors for texture, alignment, lighting, background, and domain shift; propose targeted data improvements.

Do not claim high accuracy without held-out evaluation and leakage audit. Inspired by the supplied teacher-student anomaly-detection project; no model weights or source are bundled.

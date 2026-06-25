# Railway Track Inspection - Model Comparison Report

This report compares the performance and hardware footprint of the custom Baseline CNN versus the Transfer Learning ResNet18 model on the Railway Track Inspection dataset.

---

## 1. Comparative Analysis

| Feature / Metric | Baseline CNN | Transfer Learning ResNet18 | Comparison / Delta |
| :--- | :---: | :---: | :---: |
| **Validation Accuracy** | 69.23% | 92.31% | +23.08% (ResNet18) |
| **Test Accuracy** | 61.11% | 77.78% | +16.67% (ResNet18) |
| **Test Precision** | 54.44% | 83.81% | |
| **Test Recall** | 61.11% | 77.78% | |
| **Test F1-Score** | 56.94% | 78.14% | |
| **Training Duration** | 113.1s | 119.8s | CNN is 1.1x faster |
| **Inference Latency** | 8.68 ms/img | 17.29 ms/img | CNN is 2.0x faster |
| **Model Size on Disk** | 4.88 MB | 106.79 MB | CNN is 21.9x smaller |
| **Total Parameters** | 423,044 | 11,178,564 | CNN is 26.4x lighter |
| **Trainable Parameters** | 423,044 | 11,178,564 | |
| **Peak Memory (GPU VRAM)** | 683.92 MB | 683.92 MB | |

---

## 2. Engineering Verdict & Recommendation

> [!TIP]
> **Recommended Model for Deployment**: **ResNet18**
> **Reasoning**:
> - **Accuracy**: ResNet18 achieves higher performance on the Validation dataset (92.31%).
> - **Reliability**: A pre-trained ResNet18 leverages features learned from over 1 million images on ImageNet, making it significantly more robust to variations in lighting, rust, and camera angles compared to a custom CNN trained from scratch on a small dataset.
> - **Inference Speed**: While the Baseline CNN is lighter and faster, ResNet18 handles real-time inference at **17.29 ms per image**, which is well within the requirements for live inspect-track deployment on track inspection vehicles.

### Best Model Export
The checkpoint of the recommended model has been automatically saved as **`models/best_model.pth`**. This file is a complete package and is directly ready to be loaded by the FastAPI backend in the next deployment phase.

---
*Report generated automatically on 2026-06-25 by the MLOps Model Evaluation pipeline.*

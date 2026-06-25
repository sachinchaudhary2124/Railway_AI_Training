import os
from pathlib import Path
from typing import List, Dict, Any
from fastapi import HTTPException, status
from backend.utils.config import BASE_DIR
from backend.utils.logger import logger

# Directory containing report outputs
REPORTS_DIR = BASE_DIR / "reports"

REPORT_TYPE_MAP = {
    ".md": "markdown",
    ".csv": "csv",
    ".txt": "text",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
}

REPORT_NAME_MAP = {
    "dataset_report.md": "Dataset Engineering Report",
    "training_report.md": "Training Report",
    "model_comparison.md": "Model Comparison",
    "evaluation_metrics.csv": "Evaluation Metrics",
    "classification_report.txt": "Classification Report",
    "accuracy_curve.png": "Accuracy Curve",
    "loss_curve.png": "Loss Curve",
    "confusion_matrix.png": "Confusion Matrix",
    "per_class_accuracy.png": "Per-Class Accuracy",
    "confidence_distribution.png": "Confidence Distribution",
    "class_distribution.png": "Class Distribution",
    "before_after_distribution.png": "Before and After Distribution",
    "dataset_statistics.csv": "Dataset Statistics",
    "augmentation_log.csv": "Synthetic Generation Log",
    "cleaning_log.csv": "Dataset Cleaning Log",
}

class ReportService:
    """
    Manages reporting discovery and secure download file validation.
    """
    @staticmethod
    def list_available_reports(base_url: str) -> List[Dict[str, Any]]:
        """
        Scans reports/ directory for matching standard templates.
        Returns active reports with absolute web download URLs.
        """
        if not REPORTS_DIR.exists():
            return []

        available_reports = []
        for filepath in sorted(REPORTS_DIR.iterdir(), key=lambda p: p.name.lower()):
            if not filepath.is_file():
                continue
            report_type = REPORT_TYPE_MAP.get(filepath.suffix.lower())
            if report_type is None:
                continue
            filename = filepath.name
            download_url = f"{base_url.rstrip('/')}/reports/{filename}"
            available_reports.append({
                "name": REPORT_NAME_MAP.get(filename, filename.replace("_", " ").rsplit(".", 1)[0].title()),
                "filename": filename,
                "type": report_type,
                "url": download_url
            })
        return available_reports

    @staticmethod
    def get_report_filepath(filename: str) -> Path:
        """
        Validates the filename and resolves it to a file path within REPORTS_DIR.
        Includes path traversal sanitization checks.
        """
        # 1. Path traversal protection: resolve the file only within REPORTS_DIR
        safe_filename = os.path.basename(filename)
        resolved_path = (REPORTS_DIR / safe_filename).resolve()
        
        # 2. Check if file is inside REPORTS_DIR
        try:
            resolved_path.relative_to(REPORTS_DIR.resolve())
        except ValueError:
            logger.warning(f"Path traversal attempt blocked for: {filename}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. Path traversal attempt detected."
            )
            
        # 3. Check file existence
        if not resolved_path.exists() or not resolved_path.is_file():
            logger.info(f"Report file not found: {filename}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Report file '{filename}' was not found. Please run scripts/evaluate.py first."
            )
            
        return resolved_path

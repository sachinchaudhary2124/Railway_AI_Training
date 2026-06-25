from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse
from typing import List
from backend.api.auth import get_current_user
from backend.services.report_service import ReportService
from backend.utils.schemas import ReportItem
from backend.utils.logger import logger

router = APIRouter(prefix="/reports", tags=["Inspection Reports"])

@router.get("", response_model=List[ReportItem])
async def get_all_reports(request: Request, current_user: str = Depends(get_current_user)):
    """
    Lists all available generated training, performance, and classification reports.
    """
    base_url = str(request.base_url)
    reports = ReportService.list_available_reports(base_url)
    logger.info(f"Retrieved {len(reports)} generated report templates.")
    return reports

@router.get("/{filename}")
async def download_report_file(filename: str, current_user: str = Depends(get_current_user)):
    """
    Downloads a specific report file (e.g. classification_report.txt, training_report.md, evaluation_metrics.csv).
    Includes path traversal protections.
    """
    # Get secure filepath from service
    filepath = ReportService.get_report_filepath(filename)
    
    logger.info(f"Downloading report file: {filename}")
    
    # Return file download response
    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/octet-stream"
    )

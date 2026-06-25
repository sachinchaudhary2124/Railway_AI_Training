import json
import os
import threading
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from backend.api.auth import get_current_user
from backend.utils.config import HISTORY_PATH, GRADCAM_OUTPUT_DIR
from backend.utils.schemas import HistoryItem, HistoryListResponse, MessageResponse
from backend.utils.logger import logger

router = APIRouter(prefix="/history", tags=["Prediction History"])
_history_lock = threading.Lock()

def load_history() -> List[dict]:
    """Loads prediction log array from prediction_history.json file."""
    if not HISTORY_PATH.exists():
        return []
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read prediction history file: {str(e)}")
        return []

def save_history(history_data: List[dict]):
    """Saves the prediction log list back to the local history file."""
    try:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        temp_path = HISTORY_PATH.with_suffix(".tmp")
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=4, ensure_ascii=False)
        os.replace(temp_path, HISTORY_PATH)
    except Exception as e:
        logger.error(f"Failed to write prediction history file: {str(e)}")

def append_history_item(item: dict):
    """
    Appends a single prediction record to local JSON logs.
    Runs inside BackgroundTasks to prevent request blocking.
    """
    with _history_lock:
        history = load_history()
        history.append(item)
        save_history(history)
    logger.info(f"Log appended for Prediction ID: {item['prediction_id']}")

@router.get("", response_model=HistoryListResponse)
async def get_all_history(current_user: str = Depends(get_current_user)):
    """
    Retrieves all prediction records from the local log.
    """
    history = load_history()
    # Sort history by timestamp descending (newest first)
    history_sorted = sorted(history, key=lambda x: x.get("timestamp", ""), reverse=True)
    return HistoryListResponse(history=history_sorted, total_count=len(history_sorted))

@router.get("/{prediction_id}", response_model=HistoryItem)
async def get_history_by_id(prediction_id: str, current_user: str = Depends(get_current_user)):
    """
    Retrieves a single prediction log item by its unique ID.
    """
    history = load_history()
    for item in history:
        if item.get("prediction_id") == prediction_id:
            return item
            
    logger.warning(f"History lookup failed for ID: {prediction_id}")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Prediction record with ID '{prediction_id}' was not found in the local logs."
    )

@router.delete("", response_model=MessageResponse)
async def clear_prediction_history(current_user: str = Depends(get_current_user)):
    """
    Clears all saved prediction records and removes corresponding Grad-CAM overlay images from disk.
    """
    history = load_history()
    
    # 1. Delete associated Grad-CAM files
    deleted_files_count = 0
    for item in history:
        relative_path = item.get("gradcam_path")
        if relative_path:
            # Reconstruct absolute file path
            file_basename = os.path.basename(relative_path)
            full_file_path = GRADCAM_OUTPUT_DIR / file_basename
            if full_file_path.exists():
                try:
                    os.remove(full_file_path)
                    deleted_files_count += 1
                except Exception as e:
                    logger.warning(f"Could not remove Grad-CAM file {full_file_path}: {str(e)}")
                    
    # 2. Reset JSON log file to empty array
    with _history_lock:
        save_history([])
    
    message = f"Prediction history cleared successfully. Removed {deleted_files_count} Grad-CAM overlay images from disk."
    logger.info(message)
    return MessageResponse(message=message)

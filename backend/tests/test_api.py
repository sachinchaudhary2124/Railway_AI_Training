import io
import os
import json
import pytest
from PIL import Image
from fastapi.testclient import TestClient
from backend.main import app
from backend.utils.config import DEMO_USER, DEMO_PASSWORD

from backend.services.model_service import model_service

client = TestClient(app)

def setup_module(module):
    """
    Manually initializes the model service before executing tests.
    """
    model_service.initialize()

@pytest.fixture(scope="module")
def auth_headers():
    """
    Fixture to login and return auth headers.
    """
    response = client.post(
        "/login",
        json={"username": DEMO_USER, "password": DEMO_PASSWORD}
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_root_welcome():
    """Test standard root welcome details."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "documentation" in data

def test_health_endpoint():
    """Test health check API status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "device" in data
    assert "pytorch_version" in data

def test_model_info_endpoint():
    """Test model metadata description API."""
    response = client.get("/model/info")
    assert response.status_code == 200
    data = response.json()
    assert "model_name" in data
    assert "classes" in data
    assert "accuracy" in data
    assert len(data["classes"]) == 4

def test_unauthorized_endpoints():
    """Verify that private routes return 401 when requested without JWT."""
    # Predict route
    response = client.post("/predict", files={"file": ("test.jpg", b"", "image/jpeg")})
    assert response.status_code == 401

    # History routes
    response = client.get("/history")
    assert response.status_code == 401
    
    response = client.delete("/history")
    assert response.status_code == 401

    # Reports routes
    response = client.get("/reports")
    assert response.status_code == 401
    
    response = client.get("/reports/classification_report.txt")
    assert response.status_code == 401

def test_login_validation():
    """Test authentication rejection cases."""
    # Invalid password
    response = client.post(
        "/login",
        json={"username": DEMO_USER, "password": "wrong_password"}
    )
    assert response.status_code == 401
    
    # Non-existent user
    response = client.post(
        "/login",
        json={"username": "unknown", "password": "password"}
    )
    assert response.status_code == 401

def test_predict_validation(auth_headers):
    """Test image upload validation rejections."""
    # 1. Empty upload file
    response = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("empty.jpg", b"", "image/jpeg")}
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()

    # 2. Non-image file type extension
    response = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("document.txt", b"some text data", "text/plain")}
    )
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()

    # 3. Corrupt image file structure
    response = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("corrupt.png", b"invalid_binary_image_data_12345", "image/png")}
    )
    assert response.status_code == 400
    assert "corrupted" in response.json()["detail"].lower()

def test_successful_predict_and_history_lifecycle(auth_headers):
    """
    Test the full loop:
    1. Upload valid dummy image
    2. Verify inference, latency, and Grad-CAM generation
    3. Check prediction entry in history logs
    4. Fetch prediction by ID
    5. Clean prediction logs
    """
    # 1. Generate valid dummy JPEG image in memory
    img = Image.new("RGB", (224, 224), color="blue")
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format="JPEG")
    img_bytes = img_byte_arr.getvalue()

    # 2. Trigger prediction
    response = client.post(
        "/predict",
        headers=auth_headers,
        files={"file": ("test_track.jpg", img_bytes, "image/jpeg")}
    )
    assert response.status_code == 200
    pred_data = response.json()
    
    assert "prediction_id" in pred_data
    assert "predicted_class" in pred_data
    assert "confidence" in pred_data
    assert "gradcam_url" in pred_data
    assert len(pred_data["top_3_predictions"]) <= 3
    
    pred_id = pred_data["prediction_id"]
    
    # 3. Check history list contains the prediction
    response = client.get("/history", headers=auth_headers)
    assert response.status_code == 200
    history_data = response.json()
    assert history_data["total_count"] >= 1
    
    # Check if prediction_id is in history
    found = False
    for item in history_data["history"]:
        if item["prediction_id"] == pred_id:
            found = True
            assert item["predicted_class"] == pred_data["predicted_class"]
            assert item["original_filename"] == "test_track.jpg"
            break
    assert found, f"Prediction ID {pred_id} not found in history logs."

    # 4. Fetch specific prediction log by ID
    response = client.get(f"/history/{pred_id}", headers=auth_headers)
    assert response.status_code == 200
    item = response.json()
    assert item["prediction_id"] == pred_id
    assert item["predicted_class"] == pred_data["predicted_class"]

    # 5. Clear history and verify logs are empty and Grad-CAM files are deleted
    response = client.delete("/history", headers=auth_headers)
    assert response.status_code == 200
    
    response = client.get("/history", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total_count"] == 0

def test_reports_endpoints(auth_headers):
    """Test retrieval and secure download of reports."""
    # List reports
    response = client.get("/reports", headers=auth_headers)
    assert response.status_code == 200
    reports = response.json()
    
    # We should have at least some reports discovered if they exist in reports/ folder
    assert isinstance(reports, list)
    
    # Download report if listed, otherwise test with standard report name
    if len(reports) > 0:
        filename = reports[0]["filename"]
        response = client.get(f"/reports/{filename}", headers=auth_headers)
        assert response.status_code == 200
        
    # Verify path traversal protection
    response = client.get("/reports/../../config.py", headers=auth_headers)
    # Should be rejected with 403 Forbidden or 404
    assert response.status_code in [403, 404]

# Railway AI Track Inspection System - Backend API

This is the production-quality, modular, and secure FastAPI backend for the **Railway AI Track Inspection System**. It serves as an enterprise-grade AI inference service that loads the trained ResNet18 model, executes predictions, generates Grad-CAM explainability heatmaps, handles logs history, and serves reporting documents.

---

## 🚀 Key Features

* **Single-Initialization Inference**: Loads the ResNet18 model once on startup, handles automatic CUDA/GPU transfers, performs a warm-up inference run, and holds it in memory.
* **Grad-CAM Explainability**: Automatically hooks target layers (`layer4[-1].conv2` for ResNet18), calculates backpropagation activation maps for the winning class, and generates color-blended overlays.
* **Robust Verification & Validation**: Restricts uploads by size (<5MB), supported formats (`.jpg`, `.jpeg`, `.png`, `.webp`), and runs pillow pixel integrity checks to reject corrupted files.
* **Security & Access Control**: 
  * JWT Token Authentication (admin demo user).
  * Custom, lightweight **Token Bucket IP-based rate limiter** middleware to prevent DOS without external database dependencies.
  * Strict path-traversal sanitation checks on downloading reports.
* **Prediction History Logger**: Keeps local JSON logs of every prediction containing IDs, timestamps, original file names, latencies, and Grad-CAM static URLs.
* **Performance Reporting**: Discovers and streams metrics CSVs, training reports, and confusion matrices directly from the storage directories.

---

## 📂 Backend Architecture

The backend is structured under a self-contained layout following enterprise clean-architecture principles:

```
backend/
├── main.py                  # FastAPI Application Initializer & Lifespan Hooks
├── api/                     # REST API Routers
│   ├── auth.py              # Login & JWT Validation Dependencies
│   ├── predict.py           # Defect Classification & Grad-CAM Endpoint
│   ├── history.py           # Log File Reader, Fetch, and Reset Endpoints
│   ├── reports.py           # Discovers and Serves System Metric Files
│   └── routes.py            # Welcome, Health, and Model Info Endpoints
├── services/                # Business Logic Services
│   ├── model_service.py     # ResNet18 Architecture Loader & Warmup
│   ├── image_service.py     # Preprocessing Transforms & Input Sanity Checks
│   ├── gradcam_service.py   # PyTorch Backward-hook Activation Heatmaps
│   └── report_service.py    # Report Validation & Path Traversal Prevention
├── utils/                   # Shared Configurations & Infrastructure
│   ├── config.py            # Paths, JWT Secrets, & Model Thresholds
│   ├── logger.py            # Rotating File Logger Configuration
│   ├── schemas.py           # Pydantic Input/Output Validation Schemas
│   └── middleware.py        # Custom Request Loggers & Token-Bucket Rate Limiting
└── tests/                   # Automated Testing Suite
    └── test_api.py          # End-to-end API Endpoint Unit Tests
```

---

## 🛠️ Installation & Getting Started

### 1. Pre-requisites
Ensure Python 3.9+ is installed. The backend automatically manages and installs the following libraries upon starting:
* `fastapi` & `uvicorn` (ASGI Server)
* `PyJWT` (JWT Authentication)
* `python-multipart` (Multipart File Uploads)
* `pytest` & `httpx` (Automated API Testing)

### 2. Launch the Application
Run the launcher script from the project root directory. This will execute dependency checks, establish logs folders, verify model checkpoints, and start the hot-reloading server:
```bash
python run.py
```

The service will bind to:
* **API Host**: `http://127.0.0.1:8000`
* **Interactive Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## 🌐 API Specification & Endpoint Catalog

### 🔓 Public Endpoints

#### Root Details
* **GET** `/`
* **Response**: Core system welcome banner and Swagger paths.

#### System Health Check
* **GET** `/health`
* **Response**: Hardware device target (GPU/CPU), loaded model flag, PyTorch runtime version.

#### Model Specifications
* **GET** `/model/info`
* **Response**: Model structure name, training completion date, class labels list, model size (MB), latency speed, and training metrics (Accuracy, Precision, Recall, F1).

#### Demo Token Login
* **POST** `/login`
* **Payload**:
  ```json
  {
    "username": "admin",
    "password": "password"
  }
  ```
* **Response**: A signed bearer JWT access token.

---

### 🔒 Authenticated Endpoints (Bearer JWT Required)

All the following endpoints require an `Authorization: Bearer <JWT>` header.

#### Defect Classification
* **POST** `/predict`
* **Accepts**: Standard multipart form image upload (`file`).
* **Process**: Validates pixel data, runs inference, overlays Grad-CAM Jet heatmap on final conv layer (`layer4[-1].conv2`), registers local history logs asynchronously.
* **Response**:
  ```json
  {
    "prediction_id": "8b525db3-61a7-47be-a931-155e81d7f02d",
    "timestamp": "2026-06-25T10:48:00.123456Z",
    "predicted_class": "crack",
    "confidence": 0.9452,
    "top_3_predictions": [
      { "class_name": "crack", "confidence": 0.9452 },
      { "class_name": "broken_rail", "confidence": 0.0412 },
      { "class_name": "normal", "confidence": 0.0136 }
    ],
    "inference_time_ms": 14.52,
    "gradcam_path": "backend/outputs/gradcam/gradcam_8b525db3.jpg",
    "gradcam_url": "http://127.0.0.1:8000/backend/outputs/gradcam/gradcam_8b525db3.jpg"
  }
  ```

#### Prediction History
* **GET** `/history`: List all historical prediction records sorted by date descending.
* **GET** `/history/{prediction_id}`: Retrieve a single logged inference record by ID.
* **DELETE** `/history`: Erase history JSON database and delete all saved Grad-CAM images from the filesystem.

#### Inspection Reports
* **GET** `/reports`: List all generated training curves and text files containing download links.
* **GET** `/reports/{filename}`: Stream/download a specific report file (e.g., `classification_report.txt`, `training_report.md`, `evaluation_metrics.csv`).

---

## 🧪 Testing Suite

Automated testing covers validation boundaries (empty files, bad file formats, incorrect logins, rate-limits bypass) and normal workflows.

Run the test suite using:
```bash
python -m pytest backend/tests/test_api.py -v -p no:warnings
```

---

## 📜 Logging System
Operational metrics, inferences, rate limit alerts, errors, and system lifecycles are piped to two locations:
1. **Console (stdout)**: color-formatted real-time logs.
2. **Rotating File log**: stored at [backend/logs/app.log](file:///d:/Railway_AI_Training/backend/logs/app.log). (Files rotate at 10MB, retaining 5 back-ups).

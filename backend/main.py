from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.services.model_service import model_service
from backend.utils.config import (
    CORS_ALLOWED_ORIGINS,
    CORS_ALLOWED_ORIGIN_REGEX,
    EAGER_LOAD_MODEL,
    OUTPUT_DIR,
    GRADCAM_OUTPUT_DIR,
)
from backend.utils.middleware import (
    RequestLoggingMiddleware, RateLimitingMiddleware, register_exception_handlers
)
from backend.api.auth import router as auth_router
from backend.api.predict import router as predict_router
from backend.api.history import router as history_router
from backend.api.reports import router as reports_router
from backend.api.routes import router as routes_router
from backend.utils.logger import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI Lifespan manager. Handles server startup and shutdown hooks.
    Loads and warms up the AI model only once.
    """
    logger.info("==================================================")
    logger.info("SERVER STARTUP INITIATED")
    logger.info("==================================================")
    
    # Ensure static outputs folders exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    GRADCAM_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if EAGER_LOAD_MODEL:
        try:
            model_service.initialize()
        except Exception as e:
            logger.critical(f"FATAL: Model initialization failed during startup: {str(e)}", exc_info=True)
            # We still let the server start so health check APIs work and report failures,
            # but predict routes will fail gracefully.
    else:
        logger.info("Model loading is lazy. The checkpoint will load on the first prediction request.")
        
    yield
    
    logger.info("==================================================")
    logger.info("SERVER SHUTDOWN COMPLETED")
    logger.info("==================================================")

# Initialize the core FastAPI Application
app = FastAPI(
    title="Railway Track Inspection AI Service",
    description=(
        "Production-grade REST API backend for the Railway AI Track Inspection System. "
        "Provides JWT authentication, real-time defect prediction, Grad-CAM activation map explainability, "
        "prediction history logging, and model performance reporting."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# 1. Register Global Exception Handlers
register_exception_handlers(app)

# 2. Add Middlewares (Ordered by execution flow)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)

# Enable CORS for React frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_origin_regex=CORS_ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Mount Static Output Directory (to serve Grad-CAM heatmap images)
app.mount("/backend/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

# 4. Register API Routers
app.include_router(auth_router)
app.include_router(predict_router)
app.include_router(history_router)
app.include_router(reports_router)
app.include_router(routes_router)

logger.info("FastAPI backend routers, static folders, and middlewares registered successfully.")

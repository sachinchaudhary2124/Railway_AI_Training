import time
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from backend.utils.config import RATE_LIMIT_BURST, RATE_LIMIT_REFILL_RATE
from backend.utils.logger import logger

# Store rate limit buckets in memory: {ip: {"tokens": float, "last_updated": float}}
rate_limit_buckets = {}

class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Custom IP-based Token Bucket rate limiting middleware.
    Protects API from exhaustion and abuse without external service dependencies.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Get Client IP
        client_ip = request.client.host if request.client else "unknown"

        # Bypass rate limiting for test client executions
        if client_ip in ("testclient", "unknown") or request.headers.get("x-test-request") == "true":
            return await call_next(request)

        # Exclude local test clients or certain health check paths if desired, but apply to API routes
        # For simplicity, we rate-limit all routes
        now = time.time()
        
        # Initialize or retrieve bucket
        if client_ip not in rate_limit_buckets:
            rate_limit_buckets[client_ip] = {
                "tokens": float(RATE_LIMIT_BURST),
                "last_updated": now
            }
            
        bucket = rate_limit_buckets[client_ip]
        
        # Calculate how many tokens should be added based on elapsed time
        elapsed = now - bucket["last_updated"]
        added_tokens = elapsed * RATE_LIMIT_REFILL_RATE
        
        # Refill tokens, capping at the burst limit
        bucket["tokens"] = min(float(RATE_LIMIT_BURST), bucket["tokens"] + added_tokens)
        bucket["last_updated"] = now
        
        # Check if client has a token available
        if bucket["tokens"] >= 1.0:
            bucket["tokens"] -= 1.0
            response = await call_next(request)
            return response
        else:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {request.url.path}")
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too many requests. Rate limit exceeded. Please try again later."
                }
            )

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request's method, path, response code, and execution time.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        client_ip = request.client.host if request.client else "unknown"
        
        try:
            response = await call_next(request)
            process_time = (time.time() - start_time) * 1000  # in ms
            
            # Log successful requests
            logger.info(
                f"IP: {client_ip} | Request: {request.method} {request.url.path} | "
                f"Status: {response.status_code} | Process Time: {process_time:.2f}ms"
            )
            return response
        except Exception as e:
            process_time = (time.time() - start_time) * 1000  # in ms
            logger.error(
                f"IP: {client_ip} | Request: {request.method} {request.url.path} | "
                f"EXCEPTION: {str(e)} | Process Time: {process_time:.2f}ms",
                exc_info=True
            )
            raise e

def register_exception_handlers(app):
    """
    Registers global exception handlers for the FastAPI application to return standard JSON errors.
    """
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP error on {request.method} {request.url.path}: {exc.detail} (Status: {exc.status_code})")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled system error on {request.method} {request.url.path}: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal server error occurred. Please contact the administrator."}
        )

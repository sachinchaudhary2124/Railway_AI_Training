from datetime import datetime, timedelta, timezone
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from backend.utils.config import (
    JWT_SECRET, JWT_ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, DEMO_USER, DEMO_PASSWORD
)
from backend.utils.schemas import LoginRequest, TokenResponse
from backend.utils.logger import logger

router = APIRouter(prefix="", tags=["Authentication"])
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Encodes access token payload into JWT signature.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": int(expire.timestamp())})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> str:
    """
    Decodes the JWT token and verifies signature/expiration.
    Returns the username if valid, otherwise raises HTTP 401.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload: Missing subject claim."
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Dependency to validate incoming Bearer JWT tokens.
    """
    return verify_token(credentials.credentials)

@router.post("/login", response_model=TokenResponse)
async def login(credentials: LoginRequest):
    """
    Authenticates the demo admin account and generates a JWT.
    """
    if credentials.username == DEMO_USER and credentials.password == DEMO_PASSWORD:
        access_token = create_access_token(data={"sub": credentials.username})
        logger.info(f"User '{credentials.username}' logged in successfully.")
        return TokenResponse(access_token=access_token)
    else:
        logger.warning(f"Failed login attempt for username: '{credentials.username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password."
        )

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
from config import settings
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current user (placeholder for future authentication)
    For now, this is a simple implementation that can be extended
    """
    # For development, we'll skip authentication
    # In production, you would verify JWT tokens here
    if settings.DEBUG:
        return {"user_id": "dev_user", "role": "admin"}
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # TODO: Implement proper JWT verification
    # For now, accept any token in production
    return {"user_id": "authenticated_user", "role": "user"}

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """
    Ensure the current user is an admin
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def validate_api_key(api_key: str = None):
    """
    Validate API key for external integrations
    """
    if not api_key:
        return False
    
    # For now, accept any non-empty API key
    # In production, validate against stored API keys
    return len(api_key) > 10

def get_db_session() -> Session:
    """
    Get database session with error handling
    """
    db = next(get_db())
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def validate_pagination(limit: int = 20, offset: int = 0):
    """
    Validate pagination parameters
    """
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit must be between 1 and 1000"
        )
    
    if offset < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Offset must be non-negative"
        )
    
    return {"limit": limit, "offset": offset} 
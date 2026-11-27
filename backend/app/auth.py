import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import get_settings
from app.db import execute_query

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

# In-memory token revocation blacklist (for logout functionality)
REVOKED_TOKENS = set()

def revoke_token(token: str):
    REVOKED_TOKENS.add(token)

def is_token_revoked(token: str) -> bool:
    return token in REVOKED_TOKENS

def validate_password_strength(password: str) -> Optional[str]:
    """
    Production-grade password validation:
    - Min 8 characters
    - Max 72 characters (Bcrypt truncation limit and CPU DoS mitigation)
    - Must contain at least one letter
    - Must contain at least one digit or special character
    """
    if len(password) < 8:
        return "Password must be at least 8 characters long."
    if len(password) > 72:
        return "Password must not exceed 72 characters."
    if not any(c.isalpha() for c in password):
        return "Password must contain at least one letter."
    if not any(c.isdigit() or not c.isalnum() for c in password):
        return "Password must contain at least one number or special character."
    return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None

async def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "missing_token", "message": "Authentication token is missing."}
        )

    token = credentials.credentials
    if is_token_revoked(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "token_revoked", "message": "Token has been revoked. Please sign in again."}
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "Invalid or expired authentication token."}
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "Token payload invalid."}
        )

    user = execute_query(
        "SELECT id, name, email, role, active, created_at, last_active_at FROM users WHERE id = %s",
        (user_id,),
        fetch_one=True
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "User not found."}
        )

    if not user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "account_deactivated", "message": "Your account has been deactivated."}
        )

    # Convert UUID and datetime to string
    user["id"] = str(user["id"])
    return user

async def require_admin(current_user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "forbidden", "message": "Admin privileges required."}
        )
    return current_user

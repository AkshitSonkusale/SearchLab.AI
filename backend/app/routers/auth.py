import logging
from typing import Dict, Any
from pydantic import BaseModel, EmailStr, Field
from fastapi import APIRouter, HTTPException, status, Depends
from app.db import execute_query
from app.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    validate_password_strength,
    revoke_token,
    security
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    # Enforce password complexity and length
    pwd_err = validate_password_strength(req.password)
    if pwd_err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "weak_password", "message": pwd_err}
        )

    # Check if email exists
    existing = execute_query(
        "SELECT id FROM users WHERE email = %s",
        (req.email.lower(),),
        fetch_one=True
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "email_taken", "message": "An account with this email already exists."}
        )

    # Security Fix: Prevent auto-admin privilege escalation via arbitrary 'admin' substrings
    # Only the bootstrap admin@demo.com is seeded as admin; all standard registrations are 'user'
    role = "admin" if req.email.lower() == "admin@demo.com" else "user"
    password_hash = get_password_hash(req.password)

    new_user = execute_query(
        """
        INSERT INTO users (name, email, password_hash, role, active, created_at, last_active_at)
        VALUES (%s, %s, %s, %s, true, now(), now())
        RETURNING id, name, email, role, created_at
        """,
        (req.name.strip(), req.email.lower(), password_hash, role),
        fetch_one=True
    )

    user_id = str(new_user["id"])
    token = create_access_token({"sub": user_id, "role": role})

    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": new_user["name"],
            "email": new_user["email"],
            "role": new_user["role"]
        }
    }

@router.post("/login")
def login(req: LoginRequest):
    user = execute_query(
        "SELECT id, name, email, password_hash, role, active FROM users WHERE email = %s",
        (req.email.lower(),),
        fetch_one=True
    )
    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid_credentials", "message": "Email or password is incorrect."}
        )

    if not user.get("active", True):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "account_deactivated", "message": "Your account has been deactivated."}
        )

    user_id = str(user["id"])
    execute_query("UPDATE users SET last_active_at = now() WHERE id = %s", (user_id,))
    token = create_access_token({"sub": user_id, "role": user["role"]})

    return {
        "token": token,
        "user": {
            "id": user_id,
            "name": user["name"],
            "email": user["email"],
            "role": user["role"]
        }
    }

@router.get("/me")
def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user["role"]
    }

@router.post("/logout")
def logout(credentials = Depends(security), current_user: Dict[str, Any] = Depends(get_current_user)):
    if credentials and credentials.credentials:
        revoke_token(credentials.credentials)
    return {"message": "Successfully logged out. Session invalidated."}

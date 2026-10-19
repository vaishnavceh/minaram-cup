"""
Authentication & security utilities for Minaram Cup Tournament API.
Generates and validates secure admin bearer tokens with expiration.
"""

import os
import hmac
import hashlib
import time
import json
import base64
from typing import Optional
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = os.getenv("MINARAM_JWT_SECRET", "minaram_cup_super_secret_jwt_key_2026_tkm")
ADMIN_USERNAME = os.getenv("MINARAM_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("MINARAM_ADMIN_PASSWORD", "minaram2026")

DEFAULT_ADMINS = {
    "admin": "minaram2026",
    "vaishnavvfisc@gmail.com": "popcorncinema@1",
}

security_bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash password using standard PBKDF2-HMAC-SHA256 with random salt."""
    salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"pbkdf2:sha256:{salt}:{pwd_hash}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify plain password against hashed password (supports pbkdf2 and plain text)."""
    if not hashed:
        return False
    if not hashed.startswith("pbkdf2:sha256:"):
        return hmac.compare_digest(password, hashed)
    parts = hashed.split(":")
    if len(parts) != 4:
        return False
    _, _, salt, expected_hash = parts
    calculated = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return hmac.compare_digest(calculated, expected_hash)


def authenticate_admin(username: str, password: str, db=None) -> Optional[dict]:
    """
    Authenticate administrator credentials against the database table admin_users,
    with fallback to configured default admins and environment variables.
    """
    user_clean = (username or "").strip()
    pwd_clean = (password or "").strip()
    if not user_clean or not pwd_clean:
        return None

    # 1. Database check (authoritative)
    if db:
        try:
            row = db.execute_one(
                "SELECT id, username, password_hash, role FROM admin_users WHERE LOWER(username) = LOWER(?);",
                (user_clean,)
            )
            if row and verify_password(pwd_clean, row["password_hash"]):
                return {
                    "id": row["id"],
                    "username": row["username"],
                    "role": row["role"]
                }
        except Exception:
            pass

    # 2. DEFAULT_ADMINS map fallback (case-insensitive username)
    for adm_u, adm_p in DEFAULT_ADMINS.items():
        if adm_u.lower() == user_clean.lower() and hmac.compare_digest(adm_p, pwd_clean):
            return {
                "id": 1 if adm_u == "admin" else 2,
                "username": adm_u,
                "role": "admin"
            }

    # 3. Environment variables fallback
    env_u = os.getenv("MINARAM_ADMIN_USER", "admin")
    env_p = os.getenv("MINARAM_ADMIN_PASSWORD", "minaram2026")
    if env_u.lower() == user_clean.lower() and hmac.compare_digest(env_p, pwd_clean):
        return {
            "id": 1,
            "username": env_u,
            "role": "admin"
        }

    return None


def create_access_token(username: str, expires_in_seconds: int = 86400 * 7) -> str:
    """Create a tamper-proof HMAC-SHA256 signed access token."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": username,
        "exp": int(time.time()) + expires_in_seconds,
        "iat": int(time.time()),
        "role": "admin"
    }

    h_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    signing_input = f"{h_b64}.{p_b64}".encode()

    signature = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    s_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    return f"{h_b64}.{p_b64}.{s_b64}"


def verify_token(token: str) -> Optional[dict]:
    """Verify signature and expiration of access token."""
    parts = token.split(".")
    if len(parts) != 3:
        return None

    h_b64, p_b64, s_b64 = parts
    signing_input = f"{h_b64}.{p_b64}".encode()

    expected_sig = hmac.new(SECRET_KEY.encode(), signing_input, hashlib.sha256).digest()
    # Pad s_b64
    rem = len(s_b64) % 4
    if rem > 0:
        s_b64 += "=" * (4 - rem)
    try:
        actual_sig = base64.urlsafe_b64decode(s_b64)
    except Exception:
        return None

    if not hmac.compare_digest(expected_sig, actual_sig):
        return None

    # Decode payload
    p_rem = len(p_b64) % 4
    if p_rem > 0:
        p_b64 += "=" * (4 - p_rem)
    try:
        payload = json.loads(base64.urlsafe_b64decode(p_b64).decode())
    except Exception:
        return None

    # Check expiration
    if payload.get("exp", 0) < time.time():
        return None

    return payload


async def get_current_admin(credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer)) -> dict:
    """Dependency that enforces admin authentication on private endpoints."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing administrative authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload

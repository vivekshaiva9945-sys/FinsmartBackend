import datetime as dt
import hashlib
import os
import uuid
from typing import Any
import jwt

from app.core.config import settings

# Password hashing implementation: Argon2id (Docker) -> direct bcrypt -> PBKDF2 fallback
_hasher_type: str = "pbkdf2"
_argon2_hasher = None
_bcrypt_available = False

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError
    _argon2_hasher = PasswordHasher(
        time_cost=2,
        memory_cost=65536,
        parallelism=1,
        hash_len=32,
        salt_len=16
    )
    _hasher_type = "argon2"
except ImportError:
    try:
        import bcrypt
        _bcrypt_available = True
        _hasher_type = "bcrypt"
    except ImportError:
        _hasher_type = "pbkdf2"


def hash_password(password: str) -> str:
    """Hash password using Argon2id, bcrypt, or PBKDF2."""
    if _hasher_type == "argon2" and _argon2_hasher:
        return _argon2_hasher.hash(password)
    elif _bcrypt_available:
        import bcrypt
        pw_bytes = password.encode("utf-8")[:72]
        return bcrypt.hashpw(pw_bytes, bcrypt.gensalt()).decode("utf-8")
    else:
        # Secure PBKDF2 fallback with 100,000 rounds of HMAC-SHA256
        salt = os.urandom(16).hex()
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
        return f"pbkdf2_sha256${salt}${dk.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password match against hash."""
    if not hashed_password or not plain_password:
        return False
        
    if hashed_password.startswith("$argon2"):
        if _argon2_hasher:
            try:
                return _argon2_hasher.verify(hashed_password, plain_password)
            except Exception:
                return False
        return False
    elif hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        try:
            import bcrypt
            pw_bytes = plain_password.encode("utf-8")[:72]
            return bcrypt.checkpw(pw_bytes, hashed_password.encode("utf-8"))
        except Exception:
            return False
    elif hashed_password.startswith("pbkdf2_sha256$"):
        try:
            parts = hashed_password.split("$")
            if len(parts) == 3:
                salt = parts[1]
                expected_hash = parts[2]
                dk = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), 100_000)
                return dk.hex() == expected_hash
        except Exception:
            return False
            
    # Check if argon2 hasher can verify
    if _argon2_hasher:
        try:
            return _argon2_hasher.verify(hashed_password, plain_password)
        except Exception:
            pass

    return False


def create_access_token(user_id: uuid.UUID, tenant_id: uuid.UUID, role: str, extra: dict[str, Any] | None = None) -> str:
    """Create signed JWT access token containing tenant, role and user identity."""
    now = dt.datetime.now(dt.timezone.utc)
    expire = now + dt.timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "tid": str(tenant_id),
        "role": role,
        "iat": now,
        "exp": expire,
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate JWT access token."""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])

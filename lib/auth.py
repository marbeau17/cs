import jwt
import os
from datetime import datetime, timedelta

SECRET = os.environ.get("JWT_SECRET", "cs-default-secret-change-me")
ALGORITHM = "HS256"
COOKIE_NAME = "session_token"


def create_token(user_data: dict) -> str:
    """Create a JWT token from user data. Token expires in 24 hours."""
    payload = {
        "sub": str(user_data["id"]),
        "email": user_data["email"],
        "name": user_data["name"],
        "role": user_data["role"],
        "is_admin": user_data["is_admin"],
        "exp": datetime.utcnow() + timedelta(hours=24),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGORITHM)


def verify_token(token: str):
    """Decode and validate a JWT token. Returns payload dict or None if invalid/expired."""
    try:
        return jwt.decode(token, SECRET, algorithms=[ALGORITHM])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def get_current_user(request):
    """Extract session_token from request cookies and verify it.
    Returns user dict or None.
    """
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        return None
    return verify_token(token)


def login_required(request):
    """Get the current user or return None if not authenticated.
    Caller is responsible for handling redirect when None is returned.
    """
    return get_current_user(request)


def admin_required(request):
    """Get the current user only if they are an admin.
    Returns user dict if authenticated and is_admin is True, otherwise None.
    """
    user = get_current_user(request)
    if user and user.get("is_admin") is True:
        return user
    return None

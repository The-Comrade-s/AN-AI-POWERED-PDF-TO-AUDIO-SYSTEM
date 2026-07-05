"""
Authentication helpers: registration, login, password hashing/verification.
"""
import re
import bcrypt

from database.models import get_session, User


EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""
    return bcrypt.hashpw(plain_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, AttributeError):
        return False


def validate_email(email: str) -> bool:
    return bool(EMAIL_REGEX.match(email or ""))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """Return (is_valid, message)."""
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    return True, ""


def register_user(full_name: str, email: str, password: str) -> tuple[bool, str]:
    """
    Attempt to create a new user account.
    Returns (success, message).
    """
    full_name = (full_name or "").strip()
    email = (email or "").strip().lower()

    if not full_name:
        return False, "Please enter your full name."
    if not validate_email(email):
        return False, "Please enter a valid email address."

    valid, msg = validate_password_strength(password)
    if not valid:
        return False, msg

    session = get_session()
    try:
        existing = session.query(User).filter(User.email == email).first()
        if existing:
            return False, "An account with this email already exists."

        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
        )
        session.add(user)
        session.commit()
        return True, "Account created successfully. Please log in."
    except Exception as exc:
        session.rollback()
        return False, f"Could not create account: {exc}"
    finally:
        session.close()


def authenticate_user(email: str, password: str):
    """
    Verify credentials.
    Returns (User instance or None, message).
    """
    email = (email or "").strip().lower()
    session = get_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            return None, "No account found with this email."
        if not verify_password(password, user.password_hash):
            return None, "Incorrect password."

        # Detach a lightweight snapshot so it's usable after session closes
        session.expunge(user)
        return user, "Login successful."
    finally:
        session.close()


def reset_password(email: str, new_password: str) -> tuple[bool, str]:
    """Reset a user's password (simplified 'forgot password' flow, no email verification)."""
    email = (email or "").strip().lower()
    valid, msg = validate_password_strength(new_password)
    if not valid:
        return False, msg

    session = get_session()
    try:
        user = session.query(User).filter(User.email == email).first()
        if not user:
            return False, "No account found with this email."
        user.password_hash = hash_password(new_password)
        session.commit()
        return True, "Password reset successfully. Please log in with your new password."
    except Exception as exc:
        session.rollback()
        return False, f"Could not reset password: {exc}"
    finally:
        session.close()

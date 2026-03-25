from passlib.context import CryptContext

# Global password hashing context configured for bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

__all__ = ["hash_password", "verify_password"]


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt.

    Args:
        password: Plain text password.

    Returns:
        The bcrypt hashed password string.

    Raises:
        ValueError: If the password is empty or None.
    """
    if not password:
        raise ValueError("Password must not be empty.")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash.

    Args:
        plain: Plain text password.
        hashed: Bcrypt hashed password.

    Returns:
        True if the password matches the hash, False otherwise.

    Raises:
        ValueError: If either argument is empty.
    """
    if not plain or not hashed:
        raise ValueError("Password and hash must not be empty.")
    return pwd_context.verify(plain, hashed)
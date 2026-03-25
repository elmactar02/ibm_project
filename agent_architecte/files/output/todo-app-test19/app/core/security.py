from passlib.context import CryptContext

# Configure passlib to use bcrypt for hashing passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

__all__ = ["hash_password", "verify_password"]


def hash_password(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        The bcrypt hashed password as a string.

    Raises:
        ValueError: If the password is empty or None.
    """
    if not password:
        raise ValueError("Password must not be empty.")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain text password against a bcrypt hashed password.

    Args:
        plain: The plain text password to verify.
        hashed: The bcrypt hashed password to compare against.

    Returns:
        True if the plain password matches the hashed password, False otherwise.

    Raises:
        ValueError: If either the plain or hashed password is empty or None.
    """
    if not plain or not hashed:
        raise ValueError("Both plain and hashed passwords must be provided.")
    return pwd_context.verify(plain, hashed)
from passlib.context import CryptContext


# Configure a CryptContext with bcrypt as the default scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a plain password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        The hashed password string.

    Raises:
        ValueError: If the password is empty or None.
    """
    if not password:
        raise ValueError("Password must not be empty.")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain: The plain text password to verify.
        hashed: The hashed password to compare against.

    Returns:
        True if the plain password matches the hashed password, False otherwise.

    Raises:
        ValueError: If either argument is empty or None.
    """
    if not plain or not hashed:
        raise ValueError("Both plain and hashed passwords must be provided.")
    return pwd_context.verify(plain, hashed)
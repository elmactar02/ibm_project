from passlib.context import CryptContext

# Configure passlib to use bcrypt for hashing passwords.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        A bcrypt hashed password string.

    Raises:
        ValueError: If the provided password is an empty string.
    """
    if not password:
        raise ValueError("Password must not be empty.")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain text password against a bcrypt hashed password.

    Args:
        plain: The plain text password to verify.
        hashed: The bcrypt hashed password to compare against.

    Returns:
        True if the plain password matches the hashed password, False otherwise.

    Raises:
        ValueError: If either argument is an empty string.
    """
    if not plain:
        raise ValueError("Plain password must not be empty.")
    if not hashed:
        raise ValueError("Hashed password must not be empty.")
    return pwd_context.verify(plain, hashed)
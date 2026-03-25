from passlib.context import CryptContext


# Initialize a CryptContext with the bcrypt scheme.
_pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain‑text password using bcrypt.

    Args:
        password: The plain‑text password to hash.

    Returns:
        A bcrypt‑hashed password string.

    Raises:
        ValueError: If ``password`` is an empty string.
    """
    if not password:
        raise ValueError("Password must not be empty.")
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain‑text password against a bcrypt hash.

    Args:
        plain: The plain‑text password provided by the user.
        hashed: The stored bcrypt hash to compare against.

    Returns:
        ``True`` if the password matches the hash, ``False`` otherwise.

    Raises:
        ValueError: If either ``plain`` or ``hashed`` is an empty string.
    """
    if not plain:
        raise ValueError("Plain password must not be empty.")
    if not hashed:
        raise ValueError("Hashed password must not be empty.")
    return _pwd_context.verify(plain, hashed)
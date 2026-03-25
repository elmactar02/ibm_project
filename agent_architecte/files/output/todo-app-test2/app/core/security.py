from passlib.context import CryptContext

_pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain password using bcrypt.

    Args:
        password: The plain text password to hash.

    Returns:
        The bcrypt hash string.

    Raises:
        ValueError: If ``password`` is empty or consists only of whitespace.
    """
    if not password or not password.strip():
        raise ValueError("Password must not be empty")
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain password against a bcrypt hash.

    Args:
        plain: The plain text password to verify.
        hashed: The bcrypt hashed password.

    Returns:
        ``True`` if the password matches the hash, ``False`` otherwise.

    Raises:
        ValueError: If ``plain`` or ``hashed`` is empty.
    """
    if not plain or not plain.strip():
        raise ValueError("Plain password must not be empty")
    if not hashed:
        raise ValueError("Hashed password must not be empty")
    return _pwd_context.verify(plain, hashed)


__all__: list[str] = ["hash_password", "verify_password"]
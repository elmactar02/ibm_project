from passlib.context import CryptContext

# Initialize a CryptContext with bcrypt algorithm.
_pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain‑text password using bcrypt.

    Args:
        password: The plain‑text password to hash. Must be a non‑empty string.

    Returns:
        A bcrypt‑hashed password string.

    Raises:
        TypeError: If ``password`` is not a string.
        ValueError: If ``password`` is empty or consists only of whitespace.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")
    stripped: str = password.strip()
    if not stripped:
        raise ValueError("Password cannot be empty or whitespace only")
    return _pwd_context.hash(stripped)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain‑text password against a bcrypt hash.

    Args:
        plain: The plain‑text password provided by the user.
        hashed: The bcrypt hash stored in the database.

    Returns:
        ``True`` if the password matches the hash, ``False`` otherwise.

    Raises:
        TypeError: If either ``plain`` or ``hashed`` is not a string.
        ValueError: If either argument is empty or consists only of whitespace.
    """
    if not isinstance(plain, str) or not isinstance(hashed, str):
        raise TypeError("Both plain password and hashed password must be strings")
    plain_stripped: str = plain.strip()
    hashed_stripped: str = hashed.strip()
    if not plain_stripped:
        raise ValueError("Plain password cannot be empty or whitespace only")
    if not hashed_stripped:
        raise ValueError("Hashed password cannot be empty or whitespace only")
    return _pwd_context.verify(plain_stripped, hashed_stripped)


__all__: list[str] = ["hash_password", "verify_password"]
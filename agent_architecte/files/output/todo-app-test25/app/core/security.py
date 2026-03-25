from passlib.context import CryptContext

# Initialize a CryptContext with bcrypt algorithm.
_pwd_context: CryptContext = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain‑text password using bcrypt.

    Args:
        password: The plain password to be hashed.

    Returns:
        A bcrypt‑hashed password string.

    Raises:
        TypeError: If ``password`` is not a string.
        ValueError: If ``password`` is empty.
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")
    if password == "":
        raise ValueError("Password cannot be empty.")
    return _pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plain‑text password against a bcrypt hash.

    Args:
        plain: The plain password provided by the user.
        hashed: The stored bcrypt hash to compare against.

    Returns:
        ``True`` if the password matches the hash, otherwise ``False``.

    Raises:
        TypeError: If either argument is not a string.
        ValueError: If either argument is empty.
    """
    if not isinstance(plain, str) or not isinstance(hashed, str):
        raise TypeError("Both plain password and hashed password must be strings.")
    if plain == "" or hashed == "":
        raise ValueError("Plain password and hashed password cannot be empty.")
    return _pwd_context.verify(plain, hashed)
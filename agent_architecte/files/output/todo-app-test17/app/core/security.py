from passlib.context import CryptContext

# Configure a CryptContext with bcrypt as the default scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

__all__ = ["hash_password", "verify_password"]


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    Args
    ----
    password : str
        The plaintext password to hash.

    Returns
    -------
    str
        The bcrypt hash of the password.

    Raises
    ------
    ValueError
        If the password is empty or not a string.
    """
    if not isinstance(password, str) or not password:
        raise ValueError("Password must be a non-empty string.")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a bcrypt hash.

    Args
    ----
    plain : str
        The plaintext password to verify.
    hashed : str
        The bcrypt hash to compare against.

    Returns
    -------
    bool
        True if the password matches the hash, False otherwise.

    Raises
    ------
    ValueError
        If either argument is not a string or is empty.
    """
    if not isinstance(plain, str) or not plain:
        raise ValueError("Plain password must be a non-empty string.")
    if not isinstance(hashed, str) or not hashed:
        raise ValueError("Hashed password must be a non-empty string.")
    return pwd_context.verify(plain, hashed)
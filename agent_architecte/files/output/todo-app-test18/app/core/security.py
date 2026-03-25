from passlib.context import CryptContext

# Configure passlib to use bcrypt for hashing passwords.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        A bcrypt-hashed representation of the password.

    Raises:
        ValueError: If the password is empty or None.
    """
    if not password:
        raise ValueError("Password must not be empty.")
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a plaintext password against a hashed password.

    Args:
        plain: The plaintext password to verify.
        hashed: The bcrypt-hashed password to compare against.

    Returns:
        True if the plaintext password matches the hashed password, False otherwise.

    Raises:
        ValueError: If either argument is empty or None.
    """
    if not plain or not hashed:
        raise ValueError("Both plain and hashed passwords must be provided.")
    return pwd_context.verify(plain, hashed)
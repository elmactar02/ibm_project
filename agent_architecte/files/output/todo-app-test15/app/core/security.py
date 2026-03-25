from passlib.context import CryptContext

# Configure a CryptContext with bcrypt as the default scheme
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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
        The bcrypt-hashed password.

    Raises
    ------
    ValueError
        If the password is empty or None.
    """
    if not password:
        raise ValueError("Password must not be empty.")
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """
    Verify a plaintext password against a bcrypt-hashed password.

    Args
    ----
    plain : str
        The plaintext password to verify.
    hashed : str
        The bcrypt-hashed password to compare against.

    Returns
    -------
    bool
        ``True`` if the plaintext password matches the hashed password,
        ``False`` otherwise.

    Raises
    ------
    ValueError
        If either the plaintext or hashed password is empty or None.
    """
    if not plain or not hashed:
        raise ValueError("Both plain and hashed passwords must be provided.")
    return pwd_context.verify(plain, hashed)
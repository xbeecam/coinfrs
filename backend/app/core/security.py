# /Users/cameronwong/coinfrs_v2/backend/app/core/security.py
import os
import base64
from datetime import datetime, timedelta
from jose import jwt
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from passlib.context import CryptContext

from app.core.config import settings

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain-text password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hashes a plain-text password using bcrypt."""
    return pwd_context.hash(password)

# --- JWT Token Creation ---
def create_access_token(data: dict) -> str:
    """
    Creates a JWT access token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Creates a JWT refresh token.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

# --- Key Management ---
# For production, use a dedicated key management service (e.g., AWS KMS, HashiCorp Vault).
# For local development, you must set the ENCRYPTION_KEY environment variable.
#
# To generate a secure key, run the following command in your terminal:
# $ python3 -c "import os; print(os.urandom(32).hex())"
#
# Then, set the environment variable (e.g., in your .env file or shell profile):
# export ENCRYPTION_KEY='your_generated_32_byte_hex_key'

ENCRYPTION_KEY_HEX = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY_HEX:
    raise ValueError("ENCRYPTION_KEY environment variable not set. Please generate a key and set the variable.")

try:
    # AES keys must be 32 bytes long for AES-256
    ENCRYPTION_KEY = bytes.fromhex(ENCRYPTION_KEY_HEX)
    if len(ENCRYPTION_KEY) != 32:
        raise ValueError("ENCRYPTION_KEY must be a 32-byte hex string (64 characters).")
except (ValueError, TypeError):
    raise ValueError("Invalid ENCRYPTION_KEY. Please ensure it is a 64-character hex string.")


def encrypt(plaintext: str) -> str:
    """
    Encrypts a plaintext string using AES-256-GCM.

    Args:
        plaintext: The string to encrypt.

    Returns:
        A base64-encoded string containing the nonce, ciphertext, and tag,
        formatted as 'nonce_b64.ciphertext_b64.tag_b64'.
    """
    if not isinstance(plaintext, str):
        raise TypeError("Plaintext must be a string.")

    aesgcm = AESGCM(ENCRYPTION_KEY)
    nonce = os.urandom(12)  # GCM standard nonce size is 12 bytes
    plaintext_bytes = plaintext.encode('utf-8')
    
    ciphertext = aesgcm.encrypt(nonce, plaintext_bytes, None)
    
    # Combine nonce, ciphertext, and tag for storage
    # The tag is appended to the ciphertext by AESGCM
    nonce_b64 = base64.urlsafe_b64encode(nonce).decode('utf-8')
    ciphertext_b64 = base64.urlsafe_b64encode(ciphertext).decode('utf-8')

    return f"{nonce_b64}.{ciphertext_b64}"


def decrypt(encrypted_data: str) -> str:
    """
    Decrypts a string that was encrypted with the `encrypt` function.

    Args:
        encrypted_data: The base64-encoded string ('nonce.ciphertext.tag').

    Returns:
        The original plaintext string.
    """
    if not isinstance(encrypted_data, str):
        raise TypeError("Encrypted data must be a string.")

    try:
        nonce_b64, ciphertext_b64 = encrypted_data.split('.')
    except ValueError:
        raise ValueError("Invalid encrypted data format. Expected 'nonce.ciphertext'.")

    aesgcm = AESGCM(ENCRYPTION_KEY)
    
    try:
        nonce = base64.urlsafe_b64decode(nonce_b64)
        ciphertext = base64.urlsafe_b64decode(ciphertext_b64)
        
        decrypted_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted_bytes.decode('utf-8')
    except Exception as e:
        # Broad exception to catch various crypto and decoding errors
        # In a real app, you might want to log this error for security monitoring
        raise ValueError(f"Decryption failed. The data may be tampered with or the key is incorrect. Error: {e}")


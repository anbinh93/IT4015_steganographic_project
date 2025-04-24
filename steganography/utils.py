# steganography/utils.py

from cryptography.fernet import Fernet
import base64
import logging

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Data Conversion ---

def message_to_binary(message):
    """Converts a string or bytes message to its binary string representation ('0's and '1's)."""
    if isinstance(message, str):
        try:
            # Try encoding using UTF-8 first
            message_bytes = message.encode('utf-8')
        except UnicodeEncodeError:
            logging.warning("Could not encode string as UTF-8, trying ISO-8859-1 (Latin-1).")
            # Fallback for broader character support, though less standard than UTF-8
            message_bytes = message.encode('iso-8859-1', errors='ignore')
    elif isinstance(message, bytes):
        message_bytes = message
    else:
        raise TypeError("Input must be str or bytes")

    return ''.join(format(byte, '08b') for byte in message_bytes)

def binary_to_message(binary_data):
    """Converts a binary string ('0's and '1's) back to bytes, then attempts to decode."""
    if not binary_data:
        return None # Handle empty binary string case

    # Ensure length is a multiple of 8, trim if necessary (might indicate data loss)
    remainder = len(binary_data) % 8
    if remainder != 0:
        logging.warning(f"Binary data length ({len(binary_data)}) not multiple of 8. Trimming last {remainder} bits.")
        binary_data = binary_data[:-remainder]

    if not binary_data: # Check again after potential trimming
        return None

    all_bytes_int = [int(binary_data[i: i+8], 2) for i in range(0, len(binary_data), 8)]
    message_bytes = bytearray(all_bytes_int)

    # Attempt to decode as UTF-8 first (most common)
    try:
        return message_bytes.decode('utf-8')
    except UnicodeDecodeError:
        logging.warning("Decoded data is not valid UTF-8. Trying ISO-8859-1.")
        try:
            # Try another common encoding
            return message_bytes.decode('iso-8859-1')
        except UnicodeDecodeError:
            logging.error("Could not decode data using common encodings. Returning raw bytes.")
            # If all fails, return the raw bytes
            return bytes(message_bytes) # Return immutable bytes

# --- Encryption (Using Fernet - Symmetric AES) ---

def generate_key() -> bytes:
    """Generates a secure Fernet key."""
    return Fernet.generate_key()

def encrypt_message(message_bytes: bytes, key: bytes) -> bytes:
    """Encrypts bytes using a Fernet key. Returns encrypted bytes."""
    if not isinstance(message_bytes, bytes):
        raise TypeError("Message to encrypt must be bytes.")
    if not isinstance(key, bytes):
        raise TypeError("Encryption key must be bytes.")

    try:
        f = Fernet(key)
        encrypted_message = f.encrypt(message_bytes)
        logging.info(f"Encrypted {len(message_bytes)} bytes to {len(encrypted_message)} bytes.")
        return encrypted_message
    except Exception as e:
        logging.error(f"Encryption failed: {e}")
        raise ValueError(f"Encryption failed: {e}") # Re-raise as ValueError for app handling


def decrypt_message(encrypted_message_bytes: bytes, key: bytes) -> bytes | None:
    """Decrypts bytes using a Fernet key. Returns original bytes or None on failure."""
    if not isinstance(encrypted_message_bytes, bytes):
        raise TypeError("Encrypted message must be bytes.")
    if not isinstance(key, bytes):
         raise TypeError("Decryption key must be bytes.")

    try:
        f = Fernet(key)
        decrypted_message_bytes = f.decrypt(encrypted_message_bytes)
        logging.info(f"Decrypted {len(encrypted_message_bytes)} bytes to {len(decrypted_message_bytes)} bytes.")
        return decrypted_message_bytes
    except Exception as e: # Catches InvalidToken, etc.
        logging.error(f"Decryption failed (likely incorrect key or corrupted data): {e}")
        return None # Indicate failure clearly
# steganography/lsb.py

import cv2
import numpy as np
import logging
# We no longer need binary_to_message here
from .utils import message_to_binary
from .exceptions import CapacityError, EncodingError, DecodingError

# Use a highly unlikely sequence as a delimiter
DELIMITER = "$<--STEGO-END-->$"

# --- Helper function specific to LSB decoding ---
def _binary_string_to_bytes(binary_data):
    """Converts a binary string ('0's and '1's) back to bytes."""
    if not binary_data:
        return b"" # Return empty bytes if input is empty

    # Ensure length is a multiple of 8, trim if necessary (might indicate data loss)
    remainder = len(binary_data) % 8
    if remainder != 0:
        logging.warning(f"Binary data length ({len(binary_data)}) not multiple of 8 during LSB decoding. Trimming last {remainder} bits.")
        binary_data = binary_data[:-remainder]

    if not binary_data: # Check again after potential trimming
        return b""

    try:
        # Convert segments of 8 bits into integers, then to bytes
        byte_list = [int(binary_data[i: i+8], 2) for i in range(0, len(binary_data), 8)]
        return bytes(byte_list) # Return raw bytes
    except ValueError as e:
        logging.error(f"Error converting binary string chunk to integer: {e}. Data: {binary_data[:64]}...")
        # Handle cases where a non-0/1 character might be present, though unlikely here
        raise DecodingError(f"Invalid characters found in extracted binary string: {e}")
    except Exception as e:
        logging.error(f"Unexpected error converting binary string to bytes: {e}")
        raise DecodingError(f"Could not convert extracted binary data to bytes: {e}")

# --- encode_lsb remains the same ---
def encode_lsb(img_array: np.ndarray, secret_message: bytes) -> np.ndarray:
    """
    Encodes secret bytes into an image NumPy array using LSB.
    (Code is identical to the previous version - no changes needed here)
    """
    if not isinstance(img_array, np.ndarray):
        raise TypeError("Input image must be a NumPy array.")
    if not isinstance(secret_message, bytes):
        raise TypeError("Secret message must be bytes.")
    if img_array.ndim != 3 or img_array.shape[2] != 3:
         raise ValueError("Input image must be a 3-channel (BGR) image.")

    height, width, channels = img_array.shape
    max_capacity_bits = height * width * channels
    max_capacity_bytes = max_capacity_bits // 8
    logging.info(f"Image dimensions: {width}x{height}. Max capacity: {max_capacity_bytes} bytes.")

    try:
        message_with_delimiter = secret_message + DELIMITER.encode('utf-8')
        binary_secret_message = message_to_binary(message_with_delimiter)
    except Exception as e:
        logging.error(f"Error converting message to binary: {e}")
        raise EncodingError(f"Failed to prepare message for encoding: {e}")

    required_bits = len(binary_secret_message)
    logging.info(f"Required bits (message + delimiter): {required_bits}")

    if required_bits > max_capacity_bits:
        raise CapacityError(f"Message too large. Requires {required_bits} bits, but image capacity is {max_capacity_bits} bits ({max_capacity_bytes} bytes).")

    stego_img_array = img_array.copy()
    data_index = 0

    for i in range(height):
        for j in range(width):
            for k in range(channels):
                if data_index < required_bits:
                    pixel_val = stego_img_array[i, j, k]
                    pixel_bin = format(pixel_val, '08b')
                    modified_pixel_bin = pixel_bin[:-1] + binary_secret_message[data_index]
                    stego_img_array[i, j, k] = int(modified_pixel_bin, 2)
                    data_index += 1
                else:
                    logging.info(f"Finished embedding {data_index} bits.")
                    return stego_img_array

    if data_index < required_bits:
         logging.error("Encoding finished prematurely. Not all data might be embedded.")
         raise EncodingError("Ran out of pixels before embedding all data (unexpected).")

    return stego_img_array


# --- MODIFIED decode_lsb ---
def decode_lsb(stego_img_array: np.ndarray) -> bytes | None:
    """
    Decodes secret bytes from a stego image NumPy array using LSB.

    Args:
        stego_img_array: NumPy array of the stego image (expects BGR).

    Returns:
        The decoded **encrypted** message as bytes, or None if decoding fails or no message found.

    Raises:
        DecodingError: For specific decoding issues.
        TypeError: If input is not the expected type.
    """
    if not isinstance(stego_img_array, np.ndarray):
        raise TypeError("Input stego image must be a NumPy array.")
    if stego_img_array.ndim != 3 or stego_img_array.shape[2] != 3:
         raise ValueError("Input stego image must be a 3-channel (BGR) image.")

    height, width, channels = stego_img_array.shape
    binary_data = ""
    try:
        delimiter_bin = message_to_binary(DELIMITER) # Get binary representation of delimiter
    except Exception as e:
        logging.error(f"Could not convert delimiter to binary: {e}")
        raise DecodingError("Internal error preparing delimiter for decoding.") # Should not happen

    len_delimiter_bits = len(delimiter_bin)

    logging.info("Starting LSB decoding...")

    try:
        # Iterate through pixels and channels to extract LSBs
        for i in range(height):
            for j in range(width):
                for k in range(channels):
                    pixel_val = stego_img_array[i, j, k]
                    lsb = format(pixel_val, '08b')[-1]
                    binary_data += lsb

                    # Check frequently if the delimiter has been found
                    if len(binary_data) >= len_delimiter_bits:
                        if binary_data.endswith(delimiter_bin):
                            logging.info(f"Delimiter found after extracting {len(binary_data)} bits.")
                            # Get binary data *before* the delimiter
                            secret_bin = binary_data[:-len_delimiter_bits]

                            # --- MODIFIED PART ---
                            # Convert the binary string directly to bytes
                            decoded_encrypted_bytes = _binary_string_to_bytes(secret_bin)
                            # This now correctly returns raw bytes
                            return decoded_encrypted_bytes
                            # --- END MODIFIED PART ---

        # If loop completes without finding the delimiter
        logging.warning("Reached end of image without finding delimiter.")
        raise DecodingError("Delimiter not found in the image. Is this a valid stego image?")

    except DecodingError as e:
        # Re-raise specific decoding errors
        raise e
    except Exception as e:
        logging.error(f"An unexpected error occurred during LSB extraction: {e}", exc_info=True)
        # Wrap other errors in DecodingError
        raise DecodingError(f"Error during LSB extraction process: {e}")

    # Fallback return, though should be unreachable if exceptions are raised properly
    return None
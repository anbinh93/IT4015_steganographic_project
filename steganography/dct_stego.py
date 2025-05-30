# steganography/dct_stego.py

import cv2
import numpy as np
import logging
from scipy.fftpack import dct, idct
from .utils import message_to_binary
from .exceptions import CapacityError, EncodingError, DecodingError

# DCT-based steganography is more robust than LSB
DELIMITER = "$<--STEGO-END-->$"

def _dct2(block):
    """2D DCT of a block"""
    return dct(dct(block.T, norm='ortho').T, norm='ortho')

def _idct2(block):
    """2D inverse DCT of a block"""
    return idct(idct(block.T, norm='ortho').T, norm='ortho')

def _binary_string_to_bytes(binary_data):
    """Converts a binary string ('0's and '1's) back to bytes."""
    if not binary_data:
        return b""

    remainder = len(binary_data) % 8
    if remainder != 0:
        logging.warning(f"Binary data length ({len(binary_data)}) not multiple of 8 during DCT decoding. Trimming last {remainder} bits.")
        binary_data = binary_data[:-remainder]

    if not binary_data:
        return b""

    try:
        byte_list = [int(binary_data[i: i+8], 2) for i in range(0, len(binary_data), 8)]
        return bytes(byte_list)
    except ValueError as e:
        logging.error(f"Error converting binary string chunk to integer: {e}")
        raise DecodingError(f"Invalid characters found in extracted binary string: {e}")
    except Exception as e:
        logging.error(f"Unexpected error converting binary string to bytes: {e}")
        raise DecodingError(f"Could not convert extracted binary data to bytes: {e}")

def encode_dct(img_array: np.ndarray, secret_message: bytes, quality_factor: float = 50.0) -> np.ndarray:
    """
    Encodes secret bytes into an image using DCT-based steganography.
    
    This method is more robust than LSB steganography against compression.
    
    Args:
        img_array: Input image as NumPy array (BGR format)
        secret_message: The secret data to hide (as bytes)
        quality_factor: Quality factor for embedding strength (higher = more robust, lower quality)
    
    Returns:
        Stego image as NumPy array
    
    Raises:
        CapacityError: If the image is too small for the message
        EncodingError: If encoding fails
    """
    if not isinstance(img_array, np.ndarray):
        raise TypeError("Input image must be a NumPy array.")
    if not isinstance(secret_message, bytes):
        raise TypeError("Secret message must be bytes.")
    if img_array.ndim != 3 or img_array.shape[2] != 3:
        raise ValueError("Input image must be a 3-channel (BGR) image.")
    
    height, width, channels = img_array.shape
    
    # Work with grayscale for DCT
    gray_img = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    # Calculate capacity (8x8 blocks, 1 bit per block)
    block_height = height // 8
    block_width = width // 8
    max_capacity_bits = block_height * block_width
    max_capacity_bytes = max_capacity_bits // 8
    
    logging.info(f"DCT capacity: {max_capacity_bytes} bytes ({max_capacity_bits} bits)")
    
    try:
        message_with_delimiter = secret_message + DELIMITER.encode('utf-8')
        binary_secret_message = message_to_binary(message_with_delimiter)
    except Exception as e:
        logging.error(f"Error converting message to binary: {e}")
        raise EncodingError(f"Failed to prepare message for encoding: {e}")
    
    required_bits = len(binary_secret_message)
    logging.info(f"Required bits (message + delimiter): {required_bits}")
    
    if required_bits > max_capacity_bits:
        raise CapacityError(f"Message too large. Requires {required_bits} bits, but DCT capacity is {max_capacity_bits} bits ({max_capacity_bytes} bytes).")
    
    # Create output image
    stego_img = img_array.copy()
    stego_gray = gray_img.copy()
    
    bit_index = 0
    
    # Process 8x8 blocks
    for i in range(0, block_height * 8, 8):
        for j in range(0, block_width * 8, 8):
            if bit_index >= required_bits:
                break
                
            # Extract 8x8 block
            block = stego_gray[i:i+8, j:j+8]
            
            # Apply DCT
            dct_block = _dct2(block)
            
            # Modify the DC coefficient (most significant)
            if bit_index < required_bits:
                bit_to_embed = int(binary_secret_message[bit_index])
                
                # Quantize the DC coefficient
                quantized_dc = round(dct_block[0, 0] / quality_factor)
                
                # Embed the bit by making the quantized value even/odd
                if (quantized_dc % 2) != bit_to_embed:
                    if quantized_dc % 2 == 0:
                        quantized_dc += 1
                    else:
                        quantized_dc -= 1
                
                # Update the DCT coefficient
                dct_block[0, 0] = quantized_dc * quality_factor
                
                bit_index += 1
            
            # Apply inverse DCT
            modified_block = _idct2(dct_block)
            
            # Ensure values are in valid range
            modified_block = np.clip(modified_block, 0, 255)
            
            # Put the block back
            stego_gray[i:i+8, j:j+8] = modified_block
        
        if bit_index >= required_bits:
            break
    
    # Convert back to BGR
    stego_gray_uint8 = stego_gray.astype(np.uint8)
    stego_bgr = cv2.cvtColor(stego_gray_uint8, cv2.COLOR_GRAY2BGR)
    
    logging.info(f"DCT encoding completed. Embedded {bit_index} bits.")
    return stego_bgr

def decode_dct(stego_img_array: np.ndarray, quality_factor: float = 50.0) -> bytes:
    """
    Decodes secret bytes from a stego image using DCT-based steganography.
    
    Args:
        stego_img_array: Stego image as NumPy array (BGR format)
        quality_factor: Quality factor used during encoding
    
    Returns:
        The decoded encrypted message as bytes
    
    Raises:
        DecodingError: If decoding fails or no message found
    """
    if not isinstance(stego_img_array, np.ndarray):
        raise TypeError("Input stego image must be a NumPy array.")
    if stego_img_array.ndim != 3 or stego_img_array.shape[2] != 3:
        raise ValueError("Input stego image must be a 3-channel (BGR) image.")
    
    height, width, channels = stego_img_array.shape
    
    # Work with grayscale
    gray_img = cv2.cvtColor(stego_img_array, cv2.COLOR_BGR2GRAY).astype(np.float32)
    
    try:
        delimiter_bin = message_to_binary(DELIMITER)
    except Exception as e:
        logging.error(f"Could not convert delimiter to binary: {e}")
        raise DecodingError("Internal error preparing delimiter for decoding.")
    
    len_delimiter_bits = len(delimiter_bin)
    binary_data = ""
    
    logging.info("Starting DCT decoding...")
    
    try:
        block_height = height // 8
        block_width = width // 8
        
        # Process 8x8 blocks
        for i in range(0, block_height * 8, 8):
            for j in range(0, block_width * 8, 8):
                # Extract 8x8 block
                block = gray_img[i:i+8, j:j+8]
                
                # Apply DCT
                dct_block = _dct2(block)
                
                # Extract bit from DC coefficient
                quantized_dc = round(dct_block[0, 0] / quality_factor)
                extracted_bit = str(quantized_dc % 2)
                binary_data += extracted_bit
                
                # Check if delimiter is found
                if len(binary_data) >= len_delimiter_bits:
                    if binary_data.endswith(delimiter_bin):
                        logging.info(f"Delimiter found after extracting {len(binary_data)} bits using DCT.")
                        # Get binary data before the delimiter
                        secret_bin = binary_data[:-len_delimiter_bits]
                        
                        # Convert to bytes
                        decoded_encrypted_bytes = _binary_string_to_bytes(secret_bin)
                        return decoded_encrypted_bytes
        
        # If we reach here, delimiter was not found
        logging.warning("Reached end of image without finding delimiter in DCT decoding.")
        raise DecodingError("Delimiter not found in the image. Is this a valid DCT stego image?")
        
    except DecodingError as e:
        raise e
    except Exception as e:
        logging.error(f"An unexpected error occurred during DCT extraction: {e}", exc_info=True)
        raise DecodingError(f"Error during DCT extraction process: {e}") 
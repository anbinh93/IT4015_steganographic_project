# steganography/audio_lsb.py

import numpy as np
import wave
import logging
from scipy.io import wavfile
from .utils import message_to_binary
from .exceptions import CapacityError, EncodingError, DecodingError

# Use the same delimiter as image steganography for consistency
DELIMITER = "$<--STEGO-END-->$"

def _binary_string_to_bytes(binary_data):
    """Converts a binary string ('0's and '1's) back to bytes."""
    if not binary_data:
        return b""

    remainder = len(binary_data) % 8
    if remainder != 0:
        logging.warning(f"Binary data length ({len(binary_data)}) not multiple of 8 during audio LSB decoding. Trimming last {remainder} bits.")
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

def encode_audio_lsb(audio_file_path: str, secret_message: bytes, output_path: str = None) -> str:
    """
    Encodes secret bytes into an audio file using LSB steganography.
    
    Args:
        audio_file_path: Path to the input WAV audio file
        secret_message: The secret data to hide (as bytes)
        output_path: Path for the output stego audio file (optional)
    
    Returns:
        Path to the output stego audio file
    
    Raises:
        CapacityError: If the audio file is too small for the message
        EncodingError: If encoding fails
    """
    if not isinstance(secret_message, bytes):
        raise TypeError("Secret message must be bytes.")
    
    try:
        # Read the audio file
        sample_rate, audio_data = wavfile.read(audio_file_path)
        
        # Convert to int16 if necessary
        if audio_data.dtype != np.int16:
            audio_data = audio_data.astype(np.int16)
        
        # Handle stereo audio - we'll use only the first channel
        if len(audio_data.shape) == 2:
            audio_data = audio_data[:, 0]
        
        logging.info(f"Audio file loaded: {len(audio_data)} samples, sample rate: {sample_rate}")
        
    except Exception as e:
        logging.error(f"Error loading audio file: {e}")
        raise EncodingError(f"Failed to load audio file: {e}")
    
    # Calculate capacity
    max_capacity_bits = len(audio_data)
    max_capacity_bytes = max_capacity_bits // 8
    logging.info(f"Audio capacity: {max_capacity_bytes} bytes")
    
    try:
        message_with_delimiter = secret_message + DELIMITER.encode('utf-8')
        binary_secret_message = message_to_binary(message_with_delimiter)
    except Exception as e:
        logging.error(f"Error converting message to binary: {e}")
        raise EncodingError(f"Failed to prepare message for encoding: {e}")
    
    required_bits = len(binary_secret_message)
    logging.info(f"Required bits (message + delimiter): {required_bits}")
    
    if required_bits > max_capacity_bits:
        raise CapacityError(f"Message too large. Requires {required_bits} bits, but audio capacity is {max_capacity_bits} bits ({max_capacity_bytes} bytes).")
    
    # Create a copy of the audio data
    stego_audio = audio_data.copy()
    
    # Embed the secret message
    for i in range(required_bits):
        # Modify the LSB of each audio sample
        sample_bin = format(stego_audio[i] & 0xFFFF, '016b')  # 16-bit signed
        modified_sample_bin = sample_bin[:-1] + binary_secret_message[i]
        stego_audio[i] = int(modified_sample_bin, 2)
        
        # Handle negative numbers (convert back from unsigned to signed)
        if stego_audio[i] > 32767:
            stego_audio[i] -= 65536
    
    # Save the stego audio file
    if output_path is None:
        output_path = audio_file_path.replace('.wav', '_stego.wav')
    
    try:
        wavfile.write(output_path, sample_rate, stego_audio)
        logging.info(f"Stego audio saved to: {output_path}")
        return output_path
    except Exception as e:
        logging.error(f"Error saving stego audio: {e}")
        raise EncodingError(f"Failed to save stego audio: {e}")

def decode_audio_lsb(stego_audio_path: str) -> bytes:
    """
    Decodes secret bytes from a stego audio file using LSB steganography.
    
    Args:
        stego_audio_path: Path to the stego audio file
    
    Returns:
        The decoded encrypted message as bytes
    
    Raises:
        DecodingError: If decoding fails or no message found
    """
    try:
        # Read the stego audio file
        sample_rate, stego_audio = wavfile.read(stego_audio_path)
        
        # Convert to int16 if necessary
        if stego_audio.dtype != np.int16:
            stego_audio = stego_audio.astype(np.int16)
        
        # Handle stereo audio - use only the first channel
        if len(stego_audio.shape) == 2:
            stego_audio = stego_audio[:, 0]
            
    except Exception as e:
        logging.error(f"Error loading stego audio file: {e}")
        raise DecodingError(f"Failed to load stego audio file: {e}")
    
    try:
        delimiter_bin = message_to_binary(DELIMITER)
    except Exception as e:
        logging.error(f"Could not convert delimiter to binary: {e}")
        raise DecodingError("Internal error preparing delimiter for decoding.")
    
    len_delimiter_bits = len(delimiter_bin)
    binary_data = ""
    
    logging.info("Starting audio LSB decoding...")
    
    try:
        # Extract LSBs from audio samples
        for i in range(len(stego_audio)):
            # Get the LSB of each audio sample
            sample_unsigned = stego_audio[i] & 0xFFFF  # Convert to unsigned for bit operations
            lsb = format(sample_unsigned, '016b')[-1]
            binary_data += lsb
            
            # Check if delimiter is found
            if len(binary_data) >= len_delimiter_bits:
                if binary_data.endswith(delimiter_bin):
                    logging.info(f"Delimiter found after extracting {len(binary_data)} bits from audio.")
                    # Get binary data before the delimiter
                    secret_bin = binary_data[:-len_delimiter_bits]
                    
                    # Convert to bytes
                    decoded_encrypted_bytes = _binary_string_to_bytes(secret_bin)
                    return decoded_encrypted_bytes
        
        # If we reach here, delimiter was not found
        logging.warning("Reached end of audio without finding delimiter.")
        raise DecodingError("Delimiter not found in the audio. Is this a valid stego audio file?")
        
    except DecodingError as e:
        raise e
    except Exception as e:
        logging.error(f"An unexpected error occurred during audio LSB extraction: {e}", exc_info=True)
        raise DecodingError(f"Error during audio LSB extraction process: {e}") 
"""
Steganography package for hiding data in multimedia files.

This package provides tools for:
- LSB steganography in images
- DCT-based steganography in images (robust)
- Audio LSB steganography in WAV files
- Video LSB steganography in MP4 files
- AES encryption for secure data hiding
- Support for multiple image, audio, and video formats

Author: Nguyễn Bình An, Vũ Ngọc Đức, Lê Thị Quỳnh
Version: 2.1.0
"""

from .lsb import encode_lsb, decode_lsb
from .audio_lsb import encode_audio_lsb, decode_audio_lsb
from .dct_stego import encode_dct, decode_dct
from .video_lsb import encode_video_lsb, decode_video_lsb, calculate_video_capacity, get_video_info
from .utils import generate_key, encrypt_message, decrypt_message, message_to_binary
from .exceptions import SteganographyError, CapacityError, EncodingError, DecodingError

__version__ = "2.1.0"
__all__ = [
    # Image steganography
    "encode_lsb", 
    "decode_lsb",
    "encode_dct",
    "decode_dct",
    
    # Audio steganography
    "encode_audio_lsb",
    "decode_audio_lsb",
    
    # Video steganography
    "encode_video_lsb",
    "decode_video_lsb",
    "calculate_video_capacity",
    "get_video_info",
    
    # Utilities
    "generate_key", 
    "encrypt_message", 
    "decrypt_message",
    "message_to_binary",
    
    # Exceptions
    "SteganographyError",
    "CapacityError", 
    "EncodingError", 
    "DecodingError"
] 
# steganography/video_lsb.py

import cv2
import numpy as np
import os
import logging
import tempfile
from pathlib import Path
from .utils import message_to_binary
from .exceptions import CapacityError, EncodingError, DecodingError

# Use the same delimiter as other steganography methods for consistency
DELIMITER = "$<--STEGO-END-->$"

def _binary_string_to_bytes(binary_data):
    """Converts a binary string ('0's and '1's) back to bytes."""
    if not binary_data:
        return b""

    remainder = len(binary_data) % 8
    if remainder != 0:
        logging.warning(f"Binary data length ({len(binary_data)}) not multiple of 8 during video LSB decoding. Trimming last {remainder} bits.")
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

def get_video_info(video_path: str) -> dict:
    """Get video information including frame count, fps, etc."""
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        raise ValueError(f"Could not open video file: {video_path}")
    
    info = {
        'frame_count': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
        'fps': cap.get(cv2.CAP_PROP_FPS),
        'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
        'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
        'duration': int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / cap.get(cv2.CAP_PROP_FPS)
    }
    
    cap.release()
    return info

def calculate_video_capacity(video_path: str, embed_ratio: float = 0.1) -> dict:
    """
    Calculate the capacity of a video for steganography.
    
    Args:
        video_path: Path to the video file
        embed_ratio: Ratio of frames to use for embedding (0.0 to 1.0)
    
    Returns:
        Dictionary with capacity information
    """
    info = get_video_info(video_path)
    
    # Calculate capacity per frame (LSB in each color channel)
    pixels_per_frame = info['width'] * info['height'] * 3  # RGB channels
    frames_to_use = int(info['frame_count'] * embed_ratio)
    
    total_capacity_bits = pixels_per_frame * frames_to_use
    total_capacity_bytes = total_capacity_bits // 8
    
    return {
        'total_frames': info['frame_count'],
        'frames_used': frames_to_use,
        'embed_ratio': embed_ratio,
        'pixels_per_frame': pixels_per_frame,
        'total_capacity_bits': total_capacity_bits,
        'total_capacity_bytes': total_capacity_bytes,
        'capacity_mb': total_capacity_bytes / (1024 * 1024),
        'video_info': info
    }

def encode_video_lsb(video_path: str, secret_message: bytes, output_path: str = None, 
                    embed_ratio: float = 0.1, quality: int = 90) -> str:
    """
    Encodes secret bytes into a video file using LSB steganography.
    
    Args:
        video_path: Path to the input MP4 video file
        secret_message: The secret data to hide (as bytes)
        output_path: Path for the output stego video file (optional)
        embed_ratio: Ratio of frames to use for embedding (0.0 to 1.0)
        quality: Video quality for output (0-100, higher is better)
    
    Returns:
        Path to the output stego video file
    
    Raises:
        CapacityError: If the video file is too small for the message
        EncodingError: If encoding fails
    """
    if not isinstance(secret_message, bytes):
        raise TypeError("Secret message must be bytes.")
    
    if not (0.0 < embed_ratio <= 1.0):
        raise ValueError("embed_ratio must be between 0.0 and 1.0")
    
    # Check video capacity
    try:
        capacity_info = calculate_video_capacity(video_path, embed_ratio)
        logging.info(f"Video capacity: {capacity_info['total_capacity_bytes']} bytes")
    except Exception as e:
        logging.error(f"Error analyzing video: {e}")
        raise EncodingError(f"Failed to analyze video file: {e}")
    
    # Prepare message with delimiter
    try:
        message_with_delimiter = secret_message + DELIMITER.encode('utf-8')
        binary_secret_message = message_to_binary(message_with_delimiter)
    except Exception as e:
        logging.error(f"Error converting message to binary: {e}")
        raise EncodingError(f"Failed to prepare message for encoding: {e}")
    
    required_bits = len(binary_secret_message)
    logging.info(f"Required bits (message + delimiter): {required_bits}")
    
    if required_bits > capacity_info['total_capacity_bits']:
        raise CapacityError(
            f"Message too large. Requires {required_bits} bits, "
            f"but video capacity is {capacity_info['total_capacity_bits']} bits "
            f"({capacity_info['total_capacity_bytes']} bytes)."
        )
    
    # Set output path
    if output_path is None:
        video_stem = Path(video_path).stem
        output_path = str(Path(video_path).parent / f"{video_stem}_stego.mp4")
    
    # Open input video
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise EncodingError(f"Could not open video file: {video_path}")
    
    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Setup video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        cap.release()
        raise EncodingError(f"Could not create output video: {output_path}")
    
    try:
        bit_index = 0
        frames_to_embed = int(total_frames * embed_ratio)
        frame_interval = max(1, total_frames // frames_to_embed) if frames_to_embed > 0 else total_frames
        
        logging.info(f"Embedding in {frames_to_embed} out of {total_frames} frames")
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Decide whether to embed in this frame
            should_embed = (frame_count % frame_interval == 0) and (bit_index < required_bits)
            
            if should_embed:
                # Embed data in this frame
                height, width, channels = frame.shape
                frame_bits_available = height * width * channels
                
                for i in range(height):
                    for j in range(width):
                        for k in range(channels):
                            if bit_index < required_bits:
                                # Get current pixel value
                                pixel_val = frame[i, j, k]
                                
                                # Convert to binary and modify LSB
                                pixel_bin = format(pixel_val, '08b')
                                modified_pixel_bin = pixel_bin[:-1] + binary_secret_message[bit_index]
                                frame[i, j, k] = int(modified_pixel_bin, 2)
                                
                                bit_index += 1
                            else:
                                break
                        if bit_index >= required_bits:
                            break
                    if bit_index >= required_bits:
                        break
                
                if bit_index >= required_bits:
                    logging.info(f"Finished embedding at frame {frame_count}")
            
            # Write frame to output
            out.write(frame)
            frame_count += 1
            
            # Progress logging
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                logging.info(f"Processing progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
    
    except Exception as e:
        logging.error(f"Error during video encoding: {e}")
        raise EncodingError(f"Failed during video encoding: {e}")
    
    finally:
        cap.release()
        out.release()
    
    if bit_index < required_bits:
        logging.error("Not all data was embedded in the video")
        raise EncodingError("Video capacity insufficient or encoding error occurred")
    
    logging.info(f"Successfully embedded {bit_index} bits in video")
    logging.info(f"Stego video saved to: {output_path}")
    
    return output_path

def decode_video_lsb(stego_video_path: str, embed_ratio: float = 0.1) -> bytes:
    """
    Decodes secret bytes from a stego video file using LSB steganography.
    
    Args:
        stego_video_path: Path to the stego video file
        embed_ratio: Ratio of frames used during encoding (must match encoding)
    
    Returns:
        The decoded encrypted message as bytes
    
    Raises:
        DecodingError: If decoding fails or no message found
    """
    if not (0.0 < embed_ratio <= 1.0):
        raise ValueError("embed_ratio must be between 0.0 and 1.0")
    
    # Open video
    cap = cv2.VideoCapture(stego_video_path)
    if not cap.isOpened():
        raise DecodingError(f"Could not open stego video file: {stego_video_path}")
    
    try:
        delimiter_bin = message_to_binary(DELIMITER)
    except Exception as e:
        logging.error(f"Could not convert delimiter to binary: {e}")
        raise DecodingError("Internal error preparing delimiter for decoding.")
    
    len_delimiter_bits = len(delimiter_bin)
    binary_data = ""
    
    logging.info("Starting video LSB decoding...")
    
    try:
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames_to_check = int(total_frames * embed_ratio)
        frame_interval = max(1, total_frames // frames_to_check) if frames_to_check > 0 else total_frames
        
        logging.info(f"Checking {frames_to_check} out of {total_frames} frames")
        
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Check if this frame should contain embedded data
            should_check = (frame_count % frame_interval == 0)
            
            if should_check:
                height, width, channels = frame.shape
                
                # Extract LSBs from this frame
                for i in range(height):
                    for j in range(width):
                        for k in range(channels):
                            pixel_val = frame[i, j, k]
                            lsb = format(pixel_val, '08b')[-1]
                            binary_data += lsb
                            
                            # Check for delimiter frequently
                            if len(binary_data) >= len_delimiter_bits:
                                if binary_data.endswith(delimiter_bin):
                                    logging.info(f"Delimiter found after extracting {len(binary_data)} bits from video.")
                                    # Get binary data before the delimiter
                                    secret_bin = binary_data[:-len_delimiter_bits]
                                    
                                    # Convert to bytes
                                    decoded_encrypted_bytes = _binary_string_to_bytes(secret_bin)
                                    cap.release()
                                    return decoded_encrypted_bytes
            
            frame_count += 1
            
            # Progress logging
            if frame_count % 100 == 0:
                progress = (frame_count / total_frames) * 100
                logging.info(f"Decoding progress: {progress:.1f}% ({frame_count}/{total_frames} frames)")
        
        # If we reach here, delimiter was not found
        cap.release()
        logging.warning("Reached end of video without finding delimiter.")
        raise DecodingError("Delimiter not found in the video. Is this a valid stego video file?")
        
    except DecodingError as e:
        cap.release()
        raise e
    except Exception as e:
        cap.release()
        logging.error(f"An unexpected error occurred during video LSB extraction: {e}", exc_info=True)
        raise DecodingError(f"Error during video LSB extraction process: {e}")

def extract_video_frames(video_path: str, output_dir: str, max_frames: int = 10):
    """
    Extract sample frames from video for analysis.
    
    Args:
        video_path: Path to video file
        output_dir: Directory to save frames
        max_frames: Maximum number of frames to extract
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_interval = max(1, total_frames // max_frames)
    
    frame_count = 0
    saved_count = 0
    
    while ret := cap.read()[0]:
        if frame_count % frame_interval == 0 and saved_count < max_frames:
            frame = cap.read()[1]
            frame_path = os.path.join(output_dir, f"frame_{saved_count:03d}.png")
            cv2.imwrite(frame_path, frame)
            saved_count += 1
        
        frame_count += 1
        if saved_count >= max_frames:
            break
    
    cap.release()
    logging.info(f"Extracted {saved_count} frames to {output_dir}")

def compare_videos(original_path: str, stego_path: str) -> dict:
    """
    Compare original and stego videos to analyze the impact of steganography.
    
    Args:
        original_path: Path to original video
        stego_path: Path to stego video
    
    Returns:
        Dictionary with comparison metrics
    """
    # Get video info for both
    orig_info = get_video_info(original_path)
    stego_info = get_video_info(stego_path)
    
    # Compare file sizes
    orig_size = os.path.getsize(original_path)
    stego_size = os.path.getsize(stego_path)
    
    comparison = {
        'original_info': orig_info,
        'stego_info': stego_info,
        'file_size_original': orig_size,
        'file_size_stego': stego_size,
        'size_difference': stego_size - orig_size,
        'size_ratio': stego_size / orig_size if orig_size > 0 else 0,
        'frame_count_match': orig_info['frame_count'] == stego_info['frame_count'],
        'fps_match': abs(orig_info['fps'] - stego_info['fps']) < 0.01,
        'resolution_match': (orig_info['width'] == stego_info['width'] and 
                           orig_info['height'] == stego_info['height'])
    }
    
    return comparison 
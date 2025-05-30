# tests/test_steganography.py

import unittest
import numpy as np
import tempfile
import os
import cv2
from scipy.io import wavfile

import sys
sys.path.append('..')

from steganography.lsb import encode_lsb, decode_lsb
from steganography.audio_lsb import encode_audio_lsb, decode_audio_lsb
from steganography.dct_stego import encode_dct, decode_dct
from steganography.video_lsb import encode_video_lsb, decode_video_lsb, calculate_video_capacity, get_video_info
from steganography.utils import generate_key, encrypt_message, decrypt_message, message_to_binary
from steganography.exceptions import CapacityError, EncodingError, DecodingError

class TestImageSteganography(unittest.TestCase):
    def setUp(self):
        # Create a test image (100x100 RGB)
        self.test_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        self.test_message = b"This is a secret message for testing!"
        self.key = generate_key()
    
    def test_lsb_encode_decode(self):
        """Test LSB encoding and decoding"""
        # Encrypt message
        encrypted_data = encrypt_message(self.test_message, self.key)
        
        # Encode
        stego_image = encode_lsb(self.test_image, encrypted_data)
        self.assertIsInstance(stego_image, np.ndarray)
        self.assertEqual(stego_image.shape, self.test_image.shape)
        
        # Decode
        decoded_encrypted = decode_lsb(stego_image)
        self.assertIsInstance(decoded_encrypted, bytes)
        
        # Decrypt
        decoded_message = decrypt_message(decoded_encrypted, self.key)
        self.assertEqual(decoded_message, self.test_message)
    
    def test_dct_encode_decode(self):
        """Test DCT encoding and decoding"""
        # Create larger image for DCT (need multiple 8x8 blocks)
        large_image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        
        # Encrypt message
        encrypted_data = encrypt_message(self.test_message, self.key)
        
        # Encode
        stego_image = encode_dct(large_image, encrypted_data, quality_factor=50.0)
        self.assertIsInstance(stego_image, np.ndarray)
        self.assertEqual(stego_image.shape, large_image.shape)
        
        # Decode
        decoded_encrypted = decode_dct(stego_image, quality_factor=50.0)
        self.assertIsInstance(decoded_encrypted, bytes)
        
        # Decrypt
        decoded_message = decrypt_message(decoded_encrypted, self.key)
        self.assertEqual(decoded_message, self.test_message)
    
    def test_capacity_error(self):
        """Test capacity error for large messages"""
        # Create small image
        small_image = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
        large_message = b"x" * 1000  # Large message
        
        with self.assertRaises(CapacityError):
            encode_lsb(small_image, large_message)
    
    def test_invalid_inputs(self):
        """Test handling of invalid inputs"""
        with self.assertRaises(TypeError):
            encode_lsb("not_an_array", self.test_message)
        
        with self.assertRaises(TypeError):
            encode_lsb(self.test_image, "not_bytes")

class TestAudioSteganography(unittest.TestCase):
    def setUp(self):
        self.test_message = b"Secret audio message!"
        self.key = generate_key()
        
        # Create a test WAV file
        self.temp_dir = tempfile.mkdtemp()
        self.test_audio_path = os.path.join(self.temp_dir, "test_audio.wav")
        
        # Generate test audio data (1 second, 44100 Hz, mono)
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = (np.sin(2 * np.pi * 440 * t) * 32767).astype(np.int16)
        
        wavfile.write(self.test_audio_path, sample_rate, audio_data)
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_audio_encode_decode(self):
        """Test audio LSB encoding and decoding"""
        # Encrypt message
        encrypted_data = encrypt_message(self.test_message, self.key)
        
        # Encode
        stego_audio_path = encode_audio_lsb(self.test_audio_path, encrypted_data)
        self.assertTrue(os.path.exists(stego_audio_path))
        
        # Decode
        decoded_encrypted = decode_audio_lsb(stego_audio_path)
        self.assertIsInstance(decoded_encrypted, bytes)
        
        # Decrypt
        decoded_message = decrypt_message(decoded_encrypted, self.key)
        self.assertEqual(decoded_message, self.test_message)
        
        # Clean up
        if os.path.exists(stego_audio_path):
            os.remove(stego_audio_path)
    
    def test_audio_capacity_error(self):
        """Test capacity error for audio"""
        # Create very short audio file
        short_audio_path = os.path.join(self.temp_dir, "short_audio.wav")
        short_data = np.array([1, 2, 3, 4, 5], dtype=np.int16)
        wavfile.write(short_audio_path, 44100, short_data)
        
        large_message = b"x" * 1000
        
        with self.assertRaises(CapacityError):
            encode_audio_lsb(short_audio_path, large_message)

class TestVideoSteganography(unittest.TestCase):
    def setUp(self):
        self.test_message = b"Secret video message!"
        self.key = generate_key()
        
        # Create a test video file
        self.temp_dir = tempfile.mkdtemp()
        self.test_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        
        # Create a simple test video (5 frames, 320x240)
        self.create_test_video()
    
    def create_test_video(self):
        """Create a simple test video file"""
        width, height = 320, 240
        fps = 24
        frames = 30  # 30 frames for better capacity
        
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.test_video_path, fourcc, fps, (width, height))
        
        if not out.isOpened():
            self.skipTest("Could not create test video file")
        
        # Create frames with different colors
        for i in range(frames):
            # Create a frame with gradually changing colors
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            frame[:, :, 0] = (i * 255 // frames) % 256  # Blue channel
            frame[:, :, 1] = (i * 127 // frames) % 256  # Green channel
            frame[:, :, 2] = (i * 63 // frames) % 256   # Red channel
            
            out.write(frame)
        
        out.release()
    
    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_video_info(self):
        """Test video information extraction"""
        info = get_video_info(self.test_video_path)
        
        self.assertIsInstance(info, dict)
        self.assertIn('frame_count', info)
        self.assertIn('fps', info)
        self.assertIn('width', info)
        self.assertIn('height', info)
        self.assertIn('duration', info)
        
        self.assertEqual(info['width'], 320)
        self.assertEqual(info['height'], 240)
        self.assertGreater(info['frame_count'], 0)
    
    def test_video_capacity_calculation(self):
        """Test video capacity calculation"""
        embed_ratio = 0.1
        capacity_info = calculate_video_capacity(self.test_video_path, embed_ratio)
        
        self.assertIsInstance(capacity_info, dict)
        self.assertIn('total_capacity_bytes', capacity_info)
        self.assertIn('frames_used', capacity_info)
        self.assertIn('embed_ratio', capacity_info)
        
        self.assertEqual(capacity_info['embed_ratio'], embed_ratio)
        self.assertGreater(capacity_info['total_capacity_bytes'], 0)
    
    def test_video_encode_decode(self):
        """Test video LSB encoding and decoding"""
        # Use a small message for this test
        small_message = b"Small test message"
        
        # Encrypt message
        encrypted_data = encrypt_message(small_message, self.key)
        
        # Encode with small embed ratio to ensure it fits
        embed_ratio = 0.5  # Use more frames for better capacity
        stego_video_path = encode_video_lsb(
            self.test_video_path, 
            encrypted_data, 
            embed_ratio=embed_ratio
        )
        
        self.assertTrue(os.path.exists(stego_video_path))
        
        # Decode
        decoded_encrypted = decode_video_lsb(stego_video_path, embed_ratio=embed_ratio)
        self.assertIsInstance(decoded_encrypted, bytes)
        
        # Decrypt
        decoded_message = decrypt_message(decoded_encrypted, self.key)
        self.assertEqual(decoded_message, small_message)
        
        # Clean up
        if os.path.exists(stego_video_path):
            os.remove(stego_video_path)
    
    def test_video_capacity_error(self):
        """Test capacity error for video"""
        # Try to embed a very large message
        large_message = b"x" * 100000  # 100KB message
        
        with self.assertRaises(CapacityError):
            encode_video_lsb(self.test_video_path, large_message, embed_ratio=0.01)
    
    def test_invalid_embed_ratio(self):
        """Test invalid embed ratio values"""
        message = b"test"
        
        # Test embed_ratio <= 0
        with self.assertRaises(ValueError):
            encode_video_lsb(self.test_video_path, message, embed_ratio=0.0)
        
        # Test embed_ratio > 1
        with self.assertRaises(ValueError):
            encode_video_lsb(self.test_video_path, message, embed_ratio=1.5)
    
    def test_invalid_video_file(self):
        """Test handling of invalid video files"""
        invalid_path = os.path.join(self.temp_dir, "nonexistent.mp4")
        
        with self.assertRaises(EncodingError):
            encode_video_lsb(invalid_path, b"test message")
        
        with self.assertRaises(DecodingError):
            decode_video_lsb(invalid_path)

class TestUtilities(unittest.TestCase):
    def test_message_to_binary(self):
        """Test message to binary conversion"""
        test_message = "Hello"
        binary = message_to_binary(test_message)
        self.assertIsInstance(binary, str)
        self.assertTrue(all(c in '01' for c in binary))
        self.assertEqual(len(binary), len(test_message) * 8)
    
    def test_encryption_decryption(self):
        """Test encryption and decryption"""
        test_message = b"Secret message"
        key = generate_key()
        
        # Encrypt
        encrypted = encrypt_message(test_message, key)
        self.assertIsInstance(encrypted, bytes)
        self.assertNotEqual(encrypted, test_message)
        
        # Decrypt
        decrypted = decrypt_message(encrypted, key)
        self.assertEqual(decrypted, test_message)
    
    def test_wrong_key_decryption(self):
        """Test decryption with wrong key"""
        test_message = b"Secret message"
        key1 = generate_key()
        key2 = generate_key()
        
        encrypted = encrypt_message(test_message, key1)
        decrypted = decrypt_message(encrypted, key2)
        
        self.assertIsNone(decrypted)

class TestExceptions(unittest.TestCase):
    def test_exception_hierarchy(self):
        """Test custom exception hierarchy"""
        from steganography.exceptions import SteganographyError, CapacityError, EncodingError, DecodingError
        
        # Test inheritance
        self.assertTrue(issubclass(CapacityError, SteganographyError))
        self.assertTrue(issubclass(EncodingError, SteganographyError))
        self.assertTrue(issubclass(DecodingError, SteganographyError))
        
        # Test instantiation
        try:
            raise CapacityError("Test capacity error")
        except SteganographyError as e:
            self.assertIsInstance(e, CapacityError)

if __name__ == '__main__':
    unittest.main() 
# config.py - Configuration settings for the steganography application

import os
from pathlib import Path

# Base configuration
class Config:
    """Base configuration class"""
    
    # Application settings
    APP_NAME = "Advanced StegoTool"
    APP_VERSION = "2.1.0"
    APP_DESCRIPTION = "Multimedia Steganography with Multiple Algorithms"
    
    # File paths
    BASE_DIR = Path(__file__).parent.absolute()
    TEMP_DIR = BASE_DIR / "temp"
    DEMO_DIR = BASE_DIR / "demo_image"
    TESTS_DIR = BASE_DIR / "tests"
    
    # Supported file formats
    SUPPORTED_IMAGE_FORMATS = ['png', 'bmp', 'tiff', 'jpg', 'jpeg']
    SUPPORTED_AUDIO_FORMATS = ['wav']
    SUPPORTED_VIDEO_FORMATS = ['mp4', 'avi', 'mov']
    
    # Output settings
    OUTPUT_IMAGE_FORMAT = ".png"  # Always save as lossless PNG
    OUTPUT_AUDIO_FORMAT = ".wav"
    OUTPUT_VIDEO_FORMAT = ".mp4"
    
    # Steganography settings
    DELIMITER = "$<--STEGO-END-->$"
    
    # Default algorithm parameters
    DEFAULT_DCT_QUALITY = 50.0
    DEFAULT_AUDIO_SAMPLE_RATE = 44100
    DEFAULT_VIDEO_EMBED_RATIO = 0.1
    DEFAULT_VIDEO_QUALITY = 90
    
    # Security settings
    ENCRYPTION_ALGORITHM = "AES-256"  # Via Fernet
    KEY_SIZE = 32  # bytes (256 bits)
    
    # Logging configuration
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
    
    # UI settings
    PAGE_TITLE = "Advanced StegoTool"
    PAGE_ICON = "🔐"
    LAYOUT = "wide"
    
    # Performance settings
    MAX_FILE_SIZE_MB = 500  # Increased for video files
    CHUNK_SIZE = 8192  # For file processing
    
    # Demo settings
    DEMO_IMAGE_WIDTH = 1920
    DEMO_IMAGE_HEIGHT = 1080
    DEMO_AUDIO_DURATION = 10.0  # seconds
    DEMO_VIDEO_WIDTH = 640
    DEMO_VIDEO_HEIGHT = 480
    DEMO_VIDEO_DURATION = 5.0  # seconds
    DEMO_VIDEO_FPS = 24

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    TEMP_DIR = Config.BASE_DIR / "temp_dev"
    MAX_FILE_SIZE_MB = 100  # Smaller limit for development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    # In production, use system temp directory
    TEMP_DIR = Path(os.environ.get('TEMP_DIR', '/tmp')) / "stegotool"
    MAX_FILE_SIZE_MB = 1000  # Higher limit for production

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"
    TEMP_DIR = Config.BASE_DIR / "temp_test"
    # Use smaller limits for testing
    MAX_FILE_SIZE_MB = 50
    DEMO_IMAGE_WIDTH = 256
    DEMO_IMAGE_HEIGHT = 256
    DEMO_AUDIO_DURATION = 1.0
    DEMO_VIDEO_WIDTH = 320
    DEMO_VIDEO_HEIGHT = 240
    DEMO_VIDEO_DURATION = 1.0
    DEMO_VIDEO_FPS = 24

# Algorithm-specific configurations
class AlgorithmConfig:
    """Configuration for different steganography algorithms"""
    
    LSB_CONFIG = {
        'name': 'LSB (Fast)',
        'description': 'Least Significant Bit - Fast but fragile',
        'capacity_formula': 'width × height × channels ÷ 8',
        'robustness': 'Low',
        'speed': 'Fast',
        'recommended_formats': ['png', 'bmp'],
        'avoid_formats': ['jpg', 'jpeg']
    }
    
    DCT_CONFIG = {
        'name': 'DCT (Robust)',
        'description': 'Discrete Cosine Transform - Robust but slower',
        'capacity_formula': '(width÷8) × (height÷8) ÷ 8',
        'robustness': 'High',
        'speed': 'Medium',
        'quality_range': (10.0, 100.0),
        'default_quality': 50.0,
        'recommended_formats': ['png', 'bmp', 'jpg'],
        'block_size': 8
    }
    
    AUDIO_LSB_CONFIG = {
        'name': 'Audio LSB',
        'description': 'Audio Least Significant Bit',
        'capacity_formula': 'sample_rate × duration ÷ 8',
        'robustness': 'Medium',
        'speed': 'Fast',
        'supported_formats': ['wav'],
        'sample_rates': [8000, 16000, 22050, 44100, 48000],
        'bit_depths': [16, 24, 32]
    }
    
    VIDEO_LSB_CONFIG = {
        'name': 'Video LSB',
        'description': 'Video Least Significant Bit - High capacity but slow',
        'capacity_formula': 'width × height × 3 × frames_used ÷ 8',
        'robustness': 'Low',
        'speed': 'Slow',
        'supported_formats': ['mp4', 'avi', 'mov'],
        'embed_ratio_range': (0.01, 1.0),
        'default_embed_ratio': 0.1,
        'quality_range': (10, 100),
        'default_quality': 90,
        'recommended_fps': [24, 25, 30],
        'max_resolution': (3840, 2160)  # 4K UHD
    }

# Get configuration based on environment
def get_config():
    """Get configuration based on environment variable"""
    env = os.environ.get('STEGO_ENV', 'development').lower()
    
    if env == 'production':
        return ProductionConfig()
    elif env == 'testing':
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Create temp directory if it doesn't exist
def ensure_temp_dir(config):
    """Ensure temporary directory exists"""
    config.TEMP_DIR.mkdir(parents=True, exist_ok=True)
    return config.TEMP_DIR

# Capacity calculators
class CapacityCalculator:
    """Calculate theoretical capacity for different algorithms"""
    
    @staticmethod
    def lsb_image_capacity(width: int, height: int, channels: int = 3) -> dict:
        """Calculate LSB image capacity"""
        bits = width * height * channels
        bytes_capacity = bits // 8
        return {
            'bits': bits,
            'bytes': bytes_capacity,
            'kb': bytes_capacity / 1024,
            'mb': bytes_capacity / (1024 * 1024)
        }
    
    @staticmethod
    def dct_image_capacity(width: int, height: int, block_size: int = 8) -> dict:
        """Calculate DCT image capacity"""
        blocks_width = width // block_size
        blocks_height = height // block_size
        bits = blocks_width * blocks_height
        bytes_capacity = bits // 8
        return {
            'bits': bits,
            'bytes': bytes_capacity,
            'kb': bytes_capacity / 1024,
            'mb': bytes_capacity / (1024 * 1024),
            'blocks': blocks_width * blocks_height
        }
    
    @staticmethod
    def audio_lsb_capacity(sample_rate: int, duration: float, channels: int = 1) -> dict:
        """Calculate audio LSB capacity"""
        samples = int(sample_rate * duration * channels)
        bits = samples  # 1 bit per sample
        bytes_capacity = bits // 8
        return {
            'bits': bits,
            'bytes': bytes_capacity,
            'kb': bytes_capacity / 1024,
            'mb': bytes_capacity / (1024 * 1024),
            'samples': samples
        }
    
    @staticmethod
    def video_lsb_capacity(width: int, height: int, fps: float, duration: float, 
                          embed_ratio: float = 0.1, channels: int = 3) -> dict:
        """Calculate video LSB capacity"""
        total_frames = int(fps * duration)
        frames_used = int(total_frames * embed_ratio)
        pixels_per_frame = width * height * channels
        bits = pixels_per_frame * frames_used
        bytes_capacity = bits // 8
        
        return {
            'bits': bits,
            'bytes': bytes_capacity,
            'kb': bytes_capacity / 1024,
            'mb': bytes_capacity / (1024 * 1024),
            'gb': bytes_capacity / (1024 * 1024 * 1024),
            'total_frames': total_frames,
            'frames_used': frames_used,
            'embed_ratio': embed_ratio,
            'pixels_per_frame': pixels_per_frame
        }

# Video-specific utilities
class VideoConfig:
    """Video-specific configuration and utilities"""
    
    # Standard video resolutions
    RESOLUTIONS = {
        'HD': (1280, 720),
        'FHD': (1920, 1080),
        '4K': (3840, 2160),
        'VGA': (640, 480),
        'QVGA': (320, 240)
    }
    
    # Common frame rates
    FRAME_RATES = [24, 25, 30, 50, 60]
    
    # Video quality presets
    QUALITY_PRESETS = {
        'Low': 50,
        'Medium': 70,
        'High': 85,
        'Maximum': 95
    }
    
    # Embed ratio presets
    EMBED_RATIO_PRESETS = {
        'Conservative': 0.05,  # 5% of frames
        'Balanced': 0.1,       # 10% of frames
        'Aggressive': 0.2,     # 20% of frames
        'Maximum': 0.5         # 50% of frames
    }
    
    @staticmethod
    def estimate_file_size(width: int, height: int, duration: float, 
                          fps: float, quality: int = 90) -> dict:
        """Estimate video file size based on parameters"""
        # Rough estimation based on typical compression ratios
        pixels_per_second = width * height * fps
        base_bitrate = pixels_per_second * 3 * 8  # 3 channels, 8 bits
        
        # Apply quality-based compression factor
        compression_factor = (100 - quality) / 100 * 0.95 + 0.05  # 5% to 95% compression
        compressed_bitrate = base_bitrate * compression_factor
        
        file_size_bits = compressed_bitrate * duration
        file_size_bytes = file_size_bits // 8
        
        return {
            'bytes': file_size_bytes,
            'kb': file_size_bytes / 1024,
            'mb': file_size_bytes / (1024 * 1024),
            'gb': file_size_bytes / (1024 * 1024 * 1024),
            'estimated_bitrate': compressed_bitrate
        }

# Export default configuration
config = get_config() 
# 🔐 Advanced Steganographic Data Hiding in Multimedia Files

## 👥 Group Members:
- **Nguyễn Bình An** – 20225591
- **Vũ Ngọc Đức** – 20225816
- **Lê Thị Quỳnh** – 20225917

## 🎯 Project Overview:
This project demonstrates advanced steganography techniques to hide sensitive information in various multimedia files. Our enhanced solution supports multiple algorithms and media types, providing both security and robustness for image, audio, and video files.

### 🔄 Process Flow:
1. **Encrypt**: Data is encrypted using AES-256 (Fernet) for security
2. **Add Delimiter**: Special delimiter marks data boundaries
3. **Convert to Bits**: Data converted to binary format
4. **Hide in Media**: Bits embedded using selected algorithm
5. **Save Output**: Modified media saved for transmission

For extraction:
1. **Load Media**: Load the stego media file
2. **Extract Bits**: Extract hidden bits using appropriate algorithm
3. **Find Delimiter**: Locate data boundaries
4. **Convert to Bytes**: Reconstruct original encrypted data
5. **Decrypt**: Restore original message
6. **Display**: Present decoded information

## ✨ Features:

### 🖼️ Image Steganography:
- **LSB (Least Significant Bit)**: Fast encoding, high capacity
- **DCT (Discrete Cosine Transform)**: Robust against compression
- **Multi-format support**: PNG, BMP, TIFF, JPG/JPEG

### 🎵 Audio Steganography:
- **Audio LSB**: Hide data in WAV audio files
- **High capacity**: Leverage audio sample rate
- **Stereo/Mono support**: Automatic channel handling

### 🎬 Video Steganography:
- **Video LSB**: Hide data in MP4 video files
- **Massive capacity**: Extremely high data hiding potential
- **Configurable embed ratio**: Balance between capacity and detectability
- **Frame-selective embedding**: Smart frame selection for optimal hiding
- **Progress tracking**: Real-time encoding/decoding progress

### 🔒 Security Features:
- **AES-256 Encryption**: Military-grade data protection
- **Key Management**: Secure key generation and storage
- **Custom Delimiters**: Reliable data boundary detection

### 🛠️ Technical Improvements:
- **Modular Architecture**: Clean, maintainable code structure
- **Comprehensive Error Handling**: Custom exceptions for different scenarios
- **Unit Testing**: Full test coverage for reliability
- **Performance Optimization**: Efficient algorithms and memory usage

## 📁 Project Structure:
```
steganography/
├── __init__.py              # Package initialization
├── lsb.py                  # LSB image steganography
├── audio_lsb.py            # Audio LSB steganography  
├── dct_stego.py            # DCT-based steganography
├── video_lsb.py            # Video LSB steganography (NEW!)
├── utils.py                # Encryption and utility functions
└── exceptions.py           # Custom exception classes

tests/
└── test_steganography.py   # Comprehensive unit tests

examples/
└── video_example.py        # Video steganography example

demo_image/
├── input/                  # Sample cover files
└── output/                 # Example stego outputs

app.py                      # Basic Streamlit application
app_enhanced.py             # Advanced multi-algorithm interface
requirements.txt            # Python dependencies
config.py                   # Configuration settings
run_tests.py                # Test runner
Makefile                    # Build automation
README.md                   # This file
```

## 🚀 Installation & Setup:

### 1. Clone the Repository:
```bash
git clone https://github.com/anbinh93/IT4015_steganographic_project.git
cd steganography-app
```

### 2. Create Virtual Environment (Recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies:
```bash
pip install -r requirements.txt
```

### 4. Install Additional Video Dependencies:
```bash
# For better video codec support (optional)
pip install imageio[ffmpeg] moviepy
```

## 🎮 Running the Applications:

### Basic Application:
```bash
streamlit run app.py
```

### Enhanced Application (Recommended):
```bash
streamlit run app_enhanced.py
```

### Quick Start with Make:
```bash
make install       # Install dependencies
make demo          # Create sample files
make run-enhanced  # Run the enhanced app
```

## 🧪 Running Tests:
```bash
# Run all tests
make test

# Run specific tests
make test-image    # Image steganography tests
make test-audio    # Audio steganography tests  
make test-video    # Video steganography tests (NEW!)
make test-utils    # Utility function tests

# Or use direct commands
python run_tests.py
python run_tests.py video  # Run only video tests
```

## 📊 Algorithm Comparison:

| Method | Speed | Robustness | Capacity | Detectability | Best Use Case |
|--------|--------|------------|----------|---------------|---------------|
| **LSB Image** | ⚡ Fast | ❌ Low | ✅ High | ⚠️ High | Quick prototypes |
| **DCT Image** | 🐌 Medium | ✅ High | 🔶 Medium | ✅ Low | Production use |
| **Audio LSB** | ⚡ Fast | 🔶 Medium | 🚀 Very High | 🔶 Medium | Large data |
| **Video LSB** | 🐌 Slow | ❌ Low | 🌟 Extremely High | 🔶 Medium | Massive data |

## 🔧 Advanced Usage:

### Python API Example:
```python
from steganography import encode_lsb, decode_lsb, generate_key, encrypt_message, decrypt_message
import cv2

# Load image and prepare data
image = cv2.imread('cover.png')
secret_data = b"Top secret message"
key = generate_key()

# Encrypt and encode
encrypted_data = encrypt_message(secret_data, key)
stego_image = encode_lsb(image, encrypted_data)

# Save stego image
cv2.imwrite('stego.png', stego_image)

# Later: decode and decrypt
loaded_stego = cv2.imread('stego.png')
extracted_data = decode_lsb(loaded_stego)
original_data = decrypt_message(extracted_data, key)
```

### Audio Example:
```python
from steganography.audio_lsb import encode_audio_lsb, decode_audio_lsb

# Encode
stego_path = encode_audio_lsb('cover.wav', encrypted_data)

# Decode
extracted_data = decode_audio_lsb(stego_path)
```

### Video Example:
```python
from steganography.video_lsb import encode_video_lsb, decode_video_lsb, calculate_video_capacity

# Check capacity first
capacity_info = calculate_video_capacity('cover.mp4', embed_ratio=0.1)
print(f"Video capacity: {capacity_info['capacity_mb']:.2f} MB")

# Encode with 10% of frames
stego_path = encode_video_lsb(
    'cover.mp4', 
    encrypted_data, 
    embed_ratio=0.1,
    quality=90
)

# Decode (embed_ratio must match encoding)
extracted_data = decode_video_lsb(stego_path, embed_ratio=0.1)
```

### Run Video Example:
```bash
cd examples
python video_example.py
```

## 🎯 Capacity Guidelines:

### Image Capacity:
- **LSB**: Width × Height × 3 ÷ 8 bytes
- **DCT**: (Width÷8) × (Height÷8) ÷ 8 bytes
- **Example**: 1920×1080 image
  - LSB: ~777 KB
  - DCT: ~3.7 KB

### Audio Capacity:
- **Audio LSB**: Sample Rate × Duration ÷ 8 bytes
- **Example**: 44.1kHz, 60 seconds = ~331 KB

### Video Capacity:
- **Video LSB**: Width × Height × 3 × Frames Used ÷ 8 bytes
- **Example**: 1920×1080, 30fps, 60s, 10% embed ratio = ~37 MB
- **4K Example**: 3840×2160, 24fps, 120s, 5% embed ratio = ~149 MB

### Real-world Video Capacity Examples:
| Video Type | Capacity (10% embed) | Capacity (20% embed) |
|------------|---------------------|---------------------|
| VGA 5min (640×480, 24fps) | ~3.5 MB | ~7.0 MB |
| HD 10min (1280×720, 30fps) | ~16.6 MB | ~33.2 MB |
| FHD 30min (1920×1080, 30fps) | ~149.9 MB | ~299.8 MB |
| 4K 60min (3840×2160, 24fps) | ~1.1 GB | ~2.2 GB |

## ⚠️ Security Considerations:

### 🔒 Strengths:
- **Strong Encryption**: AES-256 protects data content
- **Multiple Algorithms**: Choose based on robustness needs
- **Format Flexibility**: Support for various media types
- **Massive Capacity**: Video steganography for large datasets

### 🕵️ Limitations:
- **LSB Detection**: Statistical analysis can detect LSB usage
- **Compression Vulnerability**: Some algorithms sensitive to recompression
- **Key Management**: Secure key exchange required
- **Video Performance**: Video processing is computationally intensive

### 🛡️ Best Practices:
1. **Use DCT for critical data** (more robust against compression)
2. **Use video for large datasets** (when processing time is not critical)
3. **Keep encryption keys secure** (use secure channels)
4. **Test with target compression** (verify robustness)
5. **Use appropriate embed ratios** (balance capacity vs detectability)
6. **Consider processing resources** (video encoding requires significant CPU)

## ⚡ Performance Considerations:

### Video Steganography Performance:
- **Processing Time**: Proportional to video length and resolution
- **Memory Usage**: Requires sufficient RAM for video processing
- **Storage**: Stego videos maintain similar file sizes
- **Recommended**: Use lower embed ratios for better performance

### Optimization Tips:
- Use smaller embed ratios (5-10%) for faster processing
- Process shorter video segments for large files
- Consider resolution vs capacity trade-offs
- Use quality settings appropriate for your use case

## 🔮 Future Enhancements:

### Planned Features:
- [ ] **Advanced Video Algorithms**: Frequency domain methods
- [ ] **Batch Processing**: Process multiple files simultaneously
- [ ] **Real-time Processing**: Live video stream steganography
- [ ] **Mobile App**: Android/iOS applications
- [ ] **Cloud API**: Web service interface
- [ ] **Advanced DCT**: Multiple coefficient embedding

### Research Areas:
- [ ] **Machine Learning Detection**: Adversarial robustness
- [ ] **Quantum-Safe Encryption**: Post-quantum cryptography
- [ ] **3D Model Steganography**: Hide data in 3D objects
- [ ] **Network Steganography**: Protocol-based hiding
- [ ] **Video Compression Robustness**: Survive video re-encoding

## 📚 References & Resources:

### Academic Papers:
1. Cox, I. et al. "Digital Watermarking and Steganography" (2008)
2. Fridrich, J. "Steganography in Digital Media" (2009)
3. Ker, A. "Improved Detection of LSB Steganography" (2004)
4. Wang, H. "Video Steganography: A Review" (2019)

### Standards & Frameworks:
- **AES Encryption**: FIPS 197 Standard
- **DCT Transform**: JPEG Standard (ITU-T T.81)
- **Audio Processing**: WAV Format Specification
- **Video Processing**: MP4 Container Format

## 🤝 Contributing:

We welcome contributions! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

### Development Workflow:
```bash
make dev-setup     # Setup development environment
make dev-test      # Run formatting, linting, and tests
make clean         # Clean temporary files
```

## 📄 License:

This project is for **educational and research purposes only**. 

⚠️ **Disclaimer**: Use responsibly and in compliance with applicable laws and regulations.

---

**Advanced StegoTool v2.1** - Complete multimedia steganography with Image, Audio, and Video support.

*For questions or support, please contact the development team.*

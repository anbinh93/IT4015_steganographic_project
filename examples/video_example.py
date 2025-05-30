#!/usr/bin/env python3
# examples/video_example.py - Video Steganography Example

import sys
import os
sys.path.append('..')

import cv2
import numpy as np
from steganography.video_lsb import encode_video_lsb, decode_video_lsb, calculate_video_capacity
from steganography.utils import generate_key, encrypt_message, decrypt_message

def create_sample_video(output_path: str = "sample_video.mp4"):
    """Create a sample video for testing"""
    print("🎬 Creating sample video...")
    
    width, height = 640, 480
    fps = 24
    duration = 5  # seconds
    frames = int(fps * duration)
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    if not out.isOpened():
        print("❌ Could not create video file")
        return False
    
    # Create frames with a moving gradient
    for i in range(frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Create moving gradient effect
        for y in range(height):
            for x in range(width):
                frame[y, x, 0] = (x + i * 2) % 256  # Blue
                frame[y, x, 1] = (y + i) % 256      # Green  
                frame[y, x, 2] = (x + y + i) % 256  # Red
        
        out.write(frame)
    
    out.release()
    print(f"✅ Sample video created: {output_path}")
    return True

def video_steganography_example():
    """Demonstrate video steganography"""
    print("🔐 Video Steganography Example")
    print("=" * 40)
    
    # 1. Create sample video
    video_path = "sample_video.mp4"
    if not create_sample_video(video_path):
        return
    
    # 2. Prepare secret message
    secret_message = "This is a secret message hidden in a video file! 🎥🔒"
    print(f"📝 Secret message: {secret_message}")
    
    # 3. Generate encryption key
    key = generate_key()
    print(f"🔑 Generated encryption key")
    
    # 4. Check video capacity
    print("\n📊 Video Analysis:")
    try:
        capacity_info = calculate_video_capacity(video_path, embed_ratio=0.1)
        print(f"  - Total frames: {capacity_info['total_frames']}")
        print(f"  - Frames to use: {capacity_info['frames_used']}")
        print(f"  - Capacity: {capacity_info['capacity_mb']:.2f} MB")
        print(f"  - Total capacity: {capacity_info['total_capacity_bytes']:,} bytes")
    except Exception as e:
        print(f"❌ Error analyzing video: {e}")
        return
    
    # 5. Encrypt and encode
    print("\n🔒 Encoding process:")
    try:
        # Encrypt the message
        secret_bytes = secret_message.encode('utf-8')
        encrypted_data = encrypt_message(secret_bytes, key)
        print(f"  - Original size: {len(secret_bytes)} bytes")
        print(f"  - Encrypted size: {len(encrypted_data)} bytes")
        
        # Encode into video
        print("  - Embedding data into video... (this may take a moment)")
        stego_video_path = encode_video_lsb(
            video_path, 
            encrypted_data, 
            embed_ratio=0.1,
            quality=90
        )
        
        print(f"✅ Encoding successful!")
        print(f"  - Stego video: {stego_video_path}")
        
        # Check file sizes
        original_size = os.path.getsize(video_path)
        stego_size = os.path.getsize(stego_video_path)
        print(f"  - Original size: {original_size / 1024 / 1024:.2f} MB")
        print(f"  - Stego size: {stego_size / 1024 / 1024:.2f} MB")
        print(f"  - Size difference: {(stego_size - original_size) / 1024:.2f} KB")
        
    except Exception as e:
        print(f"❌ Encoding failed: {e}")
        return
    
    # 6. Decode and decrypt
    print("\n🔓 Decoding process:")
    try:
        # Decode from video
        print("  - Extracting data from video...")
        decoded_encrypted = decode_video_lsb(stego_video_path, embed_ratio=0.1)
        print(f"  - Extracted {len(decoded_encrypted)} bytes")
        
        # Decrypt the message
        decrypted_bytes = decrypt_message(decoded_encrypted, key)
        if decrypted_bytes is not None:
            decrypted_message = decrypted_bytes.decode('utf-8')
            print(f"✅ Decoding successful!")
            print(f"  - Recovered message: {decrypted_message}")
            
            # Verify integrity
            if decrypted_message == secret_message:
                print("✅ Message integrity verified!")
            else:
                print("❌ Message integrity check failed!")
        else:
            print("❌ Decryption failed!")
            
    except Exception as e:
        print(f"❌ Decoding failed: {e}")
        return
    
    # 7. Cleanup
    print("\n🧹 Cleaning up...")
    try:
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(stego_video_path):
            os.remove(stego_video_path)
        print("✅ Cleanup complete!")
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")

def capacity_analysis_example():
    """Show capacity analysis for different video parameters"""
    print("\n📊 Video Capacity Analysis")
    print("=" * 30)
    
    # Different video configurations
    configs = [
        {"name": "VGA (5s)", "width": 640, "height": 480, "fps": 24, "duration": 5},
        {"name": "HD (10s)", "width": 1280, "height": 720, "fps": 30, "duration": 10},
        {"name": "FHD (30s)", "width": 1920, "height": 1080, "fps": 30, "duration": 30},
        {"name": "4K (60s)", "width": 3840, "height": 2160, "fps": 24, "duration": 60},
    ]
    
    embed_ratios = [0.05, 0.1, 0.2]
    
    print(f"{'Video':<12} {'Embed%':<8} {'Frames Used':<12} {'Capacity':<12}")
    print("-" * 50)
    
    for config in configs:
        for ratio in embed_ratios:
            total_frames = int(config['fps'] * config['duration'])
            frames_used = int(total_frames * ratio)
            pixels_per_frame = config['width'] * config['height'] * 3
            capacity_bytes = (pixels_per_frame * frames_used) // 8
            
            print(f"{config['name']:<12} {ratio*100:>5.0f}%   {frames_used:>8}    {capacity_bytes/1024/1024:>8.1f} MB")

if __name__ == "__main__":
    try:
        # Run the main example
        video_steganography_example()
        
        # Show capacity analysis
        capacity_analysis_example()
        
        print("\n🎉 Video steganography example completed!")
        print("\nNote: Video steganography is best suited for:")
        print("  - Large data that needs to be hidden")
        print("  - Applications where processing time is not critical")
        print("  - Scenarios where video files are common")
        
    except KeyboardInterrupt:
        print("\n⚠️  Example interrupted by user")
    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc() 
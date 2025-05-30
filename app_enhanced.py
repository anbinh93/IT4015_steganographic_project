# app_enhanced.py - Enhanced Steganography Tool

import streamlit as st
import cv2
import numpy as np
import os
import io
import logging
import base64
import tempfile
from pathlib import Path

# Import local modules
from steganography.lsb import encode_lsb, decode_lsb
from steganography.audio_lsb import encode_audio_lsb, decode_audio_lsb
from steganography.dct_stego import encode_dct, decode_dct
from steganography.video_lsb import encode_video_lsb, decode_video_lsb, calculate_video_capacity, get_video_info
from steganography.utils import (
    generate_key, encrypt_message, decrypt_message
)
from steganography.exceptions import CapacityError, EncodingError, DecodingError, SteganographyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
OUTPUT_FORMAT = ".png"
ALLOWED_IMAGE_TYPES = ['png', 'bmp', 'tiff', 'jpg', 'jpeg']
ALLOWED_AUDIO_TYPES = ['wav']
ALLOWED_VIDEO_TYPES = ['mp4', 'avi', 'mov']

# --- Enhanced Helper Functions ---
def load_image_from_upload(uploaded_file):
    if uploaded_file is not None:
        try:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is None:
                st.error("Could not decode image. Is the file format correct and supported?")
                return None
            return img
        except Exception as e:
            st.error(f"Error loading image: {e}")
            logging.error(f"Failed to load/decode uploaded image: {e}", exc_info=True)
            return None
    return None

def save_uploaded_file(uploaded_file, directory="temp"):
    """Save uploaded file to temporary directory and return path"""
    if uploaded_file is not None:
        if not os.path.exists(directory):
            os.makedirs(directory)
        
        file_path = os.path.join(directory, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        return file_path
    return None

def get_image_download_bytes(img_array_bgr, format=OUTPUT_FORMAT):
    try:
        is_success, buffer = cv2.imencode(format, img_array_bgr)
        if not is_success:
            raise ValueError("cv2.imencode failed")
        return buffer.tobytes()
    except Exception as e:
        st.error(f"Could not prepare image for download: {e}")
        logging.error(f"cv2.imencode failed: {e}", exc_info=True)
        return None

def display_key_management(widget_key_prefix: str):
    st.subheader("🔑 Encryption Key")
    if 'encryption_key' not in st.session_state or not st.session_state.encryption_key:
        st.session_state.encryption_key = base64.urlsafe_b64encode(generate_key()).decode('utf-8')

    key_input_key = f"{widget_key_prefix}_key_display"
    generate_button_key = f"{widget_key_prefix}_generate_key"

    st.text_input("Current Key (Keep this secret!)",
                  value=st.session_state.encryption_key,
                  key=key_input_key,
                  type="password",
                  on_change=lambda: st.session_state.update(encryption_key=st.session_state[key_input_key]),
                  help="Copy this key to use for decoding.")

    if st.button("Generate New Key", key=generate_button_key):
        st.session_state.encryption_key = base64.urlsafe_b64encode(generate_key()).decode('utf-8')
        st.rerun()

    try:
        key_bytes = base64.urlsafe_b64decode(st.session_state.encryption_key.encode('utf-8'))
        return key_bytes
    except Exception as e:
        st.error(f"Invalid key format stored in session state: {e}")
        st.session_state.encryption_key = base64.urlsafe_b64encode(generate_key()).decode('utf-8')
        st.warning("Key format was invalid, generated a new one.")
        st.rerun()
        return None

# --- Streamlit App UI ---
st.set_page_config(page_title="Advanced StegoTool", layout="wide", page_icon="🔐")
st.title("🔐 Advanced StegoTool: Multimedia Steganography")
st.caption("Hide secrets in Images, Audio, and Video with multiple algorithms")

# Sidebar for method selection
st.sidebar.header("🛠️ Configuration")
media_type = st.sidebar.selectbox("Media Type:", ["Image", "Audio", "Video"])

if media_type == "Image":
    stego_method = st.sidebar.selectbox(
        "Steganography Method:", 
        ["LSB (Fast)", "DCT (Robust)"],
        help="LSB is faster but less robust. DCT is slower but more resistant to compression."
    )
elif media_type == "Audio":
    stego_method = "Audio LSB"
else:  # Video
    stego_method = "Video LSB"

# Quality setting for DCT
if stego_method == "DCT (Robust)":
    quality_factor = st.sidebar.slider(
        "Quality Factor:", 
        min_value=10.0, 
        max_value=100.0, 
        value=50.0,
        help="Higher values = more robust but lower image quality"
    )

# Video-specific settings
if media_type == "Video":
    embed_ratio = st.sidebar.slider(
        "Embed Ratio:", 
        min_value=0.01, 
        max_value=1.0, 
        value=0.1,
        help="Fraction of frames to use for embedding (higher = more capacity but more detectable)"
    )
    
    video_quality = st.sidebar.slider(
        "Output Video Quality:", 
        min_value=10, 
        max_value=100, 
        value=90,
        help="Output video quality (higher = better quality but larger file)"
    )

tab1, tab2, tab3 = st.tabs(["🔒 Encode", "🔓 Decode", "📊 Analysis"])

# --- ENCODE TAB ---
with tab1:
    st.header(f"Encode Message using {stego_method}")
    
    if media_type == "Image":
        st.markdown("Upload a cover image and provide the secret data.")
    elif media_type == "Audio":
        st.markdown("Upload a cover audio file (WAV format) and provide the secret data.")
    else:  # Video
        st.markdown("Upload a cover video file (MP4 format) and provide the secret data.")

    key_bytes_encode = display_key_management(widget_key_prefix="encode")

    st.subheader("1. Select Secret Data")
    input_method = st.radio("Secret Input Method:", ("Text Message", "Upload File"), horizontal=True, key="enc_input")

    secret_data_bytes = None
    if input_method == "Text Message":
        secret_text = st.text_area("Enter Secret Text:", height=100, key="enc_text")
        if secret_text:
            try:
                secret_data_bytes = secret_text.encode('utf-8')
            except Exception as e:
                st.error(f"Could not encode text: {e}")
    else:
        secret_file = st.file_uploader("Upload Secret File:", key="enc_file_secret")
        if secret_file is not None:
            secret_data_bytes = secret_file.getvalue()

    st.subheader("2. Upload Cover Media")
    
    if media_type == "Image":
        uploaded_cover = st.file_uploader(
            "Choose Cover Image:",
            type=ALLOWED_IMAGE_TYPES,
            key="enc_file_cover"
        )
        
        if uploaded_cover and uploaded_cover.type in ["image/jpeg", "image/jpg"]:
            st.warning("⚠️ **Warning:** JPEG/JPG may not preserve hidden data if re-compressed.")
            
    elif media_type == "Audio":
        uploaded_cover = st.file_uploader(
            "Choose Cover Audio (WAV):",
            type=ALLOWED_AUDIO_TYPES,
            key="enc_audio_cover"
        )
    else:  # Video
        uploaded_cover = st.file_uploader(
            "Choose Cover Video (MP4):",
            type=ALLOWED_VIDEO_TYPES,
            key="enc_video_cover"
        )
        
        # Show video info if uploaded
        if uploaded_cover:
            temp_video_path = save_uploaded_file(uploaded_cover, "temp")
            if temp_video_path:
                try:
                    video_info = get_video_info(temp_video_path)
                    capacity_info = calculate_video_capacity(temp_video_path, embed_ratio)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.info(f"""
                        **Video Info:**
                        - Resolution: {video_info['width']}×{video_info['height']}
                        - Duration: {video_info['duration']:.1f} seconds
                        - Frames: {video_info['frame_count']}
                        - FPS: {video_info['fps']:.1f}
                        """)
                    
                    with col2:
                        st.info(f"""
                        **Capacity Info:**
                        - Frames to use: {capacity_info['frames_used']}
                        - Capacity: {capacity_info['capacity_mb']:.2f} MB
                        - Total capacity: {capacity_info['total_capacity_bytes']:,} bytes
                        """)
                    
                    # Preview video
                    st.video(uploaded_cover.getvalue())
                    
                except Exception as e:
                    st.error(f"Error analyzing video: {e}")
                finally:
                    if os.path.exists(temp_video_path):
                        os.remove(temp_video_path)

    st.subheader("3. Encode")
    encode_button = st.button("Encode Media", key="enc_button", 
                             disabled=(not uploaded_cover or not secret_data_bytes or not key_bytes_encode))

    if encode_button:
        if uploaded_cover and secret_data_bytes and key_bytes_encode:
            try:
                with st.spinner("Encrypting data..."):
                    encrypted_data = encrypt_message(secret_data_bytes, key_bytes_encode)
                st.info(f"Data encrypted ({len(secret_data_bytes)} -> {len(encrypted_data)} bytes).")

                if media_type == "Image":
                    cover_img_bgr = load_image_from_upload(uploaded_cover)
                    if cover_img_bgr is not None:
                        st.image(cv2.cvtColor(cover_img_bgr, cv2.COLOR_BGR2RGB), 
                                caption="Original Cover Image", use_container_width=True)

                        with st.spinner(f"Encoding data using {stego_method}..."):
                            if stego_method == "LSB (Fast)":
                                stego_img_bgr = encode_lsb(cover_img_bgr, encrypted_data)
                            else:  # DCT
                                stego_img_bgr = encode_dct(cover_img_bgr, encrypted_data, quality_factor)

                        st.success("Encoding successful!")
                        st.image(cv2.cvtColor(stego_img_bgr, cv2.COLOR_BGR2RGB), 
                                caption=f"Stego Image ({stego_method})", use_container_width=True)

                        download_bytes = get_image_download_bytes(stego_img_bgr, format=".png")
                        if download_bytes:
                            st.download_button(
                                label="Download Stego Image (PNG)",
                                data=download_bytes,
                                file_name=f"stego_{stego_method.lower().replace(' ', '_')}_{os.path.splitext(uploaded_cover.name)[0]}.png",
                                mime="image/png"
                            )

                elif media_type == "Audio":
                    # Audio processing
                    temp_audio_path = save_uploaded_file(uploaded_cover, "temp")
                    
                    if temp_audio_path:
                        st.audio(uploaded_cover.getvalue(), format='audio/wav')
                        
                        with st.spinner("Encoding data into audio..."):
                            stego_audio_path = encode_audio_lsb(temp_audio_path, encrypted_data)

                        st.success("Audio encoding successful!")
                        
                        # Provide download for stego audio
                        with open(stego_audio_path, 'rb') as f:
                            stego_audio_bytes = f.read()
                        
                        st.download_button(
                            label="Download Stego Audio (WAV)",
                            data=stego_audio_bytes,
                            file_name=f"stego_{os.path.splitext(uploaded_cover.name)[0]}.wav",
                            mime="audio/wav"
                        )
                        
                        # Cleanup
                        if os.path.exists(temp_audio_path):
                            os.remove(temp_audio_path)
                        if os.path.exists(stego_audio_path):
                            os.remove(stego_audio_path)

                else:  # Video
                    # Video processing
                    temp_video_path = save_uploaded_file(uploaded_cover, "temp")
                    
                    if temp_video_path:
                        # Show progress bar for video processing
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        with st.spinner("Encoding data into video... This may take several minutes."):
                            stego_video_path = encode_video_lsb(
                                temp_video_path, 
                                encrypted_data, 
                                embed_ratio=embed_ratio,
                                quality=video_quality
                            )

                        st.success("Video encoding successful!")
                        
                        # Provide download for stego video
                        with open(stego_video_path, 'rb') as f:
                            stego_video_bytes = f.read()
                        
                        file_size_mb = len(stego_video_bytes) / (1024 * 1024)
                        st.info(f"Stego video size: {file_size_mb:.2f} MB")
                        
                        st.download_button(
                            label="Download Stego Video (MP4)",
                            data=stego_video_bytes,
                            file_name=f"stego_{os.path.splitext(uploaded_cover.name)[0]}.mp4",
                            mime="video/mp4"
                        )
                        
                        # Cleanup
                        if os.path.exists(temp_video_path):
                            os.remove(temp_video_path)
                        if os.path.exists(stego_video_path):
                            os.remove(stego_video_path)

            except CapacityError as e:
                st.error(f"Encoding Failed: {e}")
            except (EncodingError, SteganographyError, ValueError, TypeError) as e:
                st.error(f"Encoding Failed: {e}")
                logging.error("Encoding process failed.", exc_info=True)
            except Exception as e:
                st.error(f"An unexpected error occurred during encoding: {e}")
                logging.error("Unexpected encoding error.", exc_info=True)

# --- DECODE TAB ---
with tab2:
    st.header(f"Decode Message using {stego_method}")
    
    key_bytes_decode = display_key_management(widget_key_prefix="decode")

    st.subheader("1. Upload Stego Media")
    
    if media_type == "Image":
        uploaded_stego = st.file_uploader(
            "Choose Stego Image:",
            type=ALLOWED_IMAGE_TYPES,
            key="dec_file_stego"
        )
    elif media_type == "Audio":
        uploaded_stego = st.file_uploader(
            "Choose Stego Audio:",
            type=ALLOWED_AUDIO_TYPES,
            key="dec_audio_stego"
        )
    else:  # Video
        uploaded_stego = st.file_uploader(
            "Choose Stego Video:",
            type=ALLOWED_VIDEO_TYPES,
            key="dec_video_stego"
        )
        
        # Video-specific decode settings
        if uploaded_stego:
            st.subheader("Video Decode Settings")
            decode_embed_ratio = st.slider(
                "Embed Ratio (must match encoding):", 
                min_value=0.01, 
                max_value=1.0, 
                value=0.1,
                key="decode_embed_ratio",
                help="Must match the ratio used during encoding"
            )

    st.subheader("2. Decode")
    decode_button = st.button("Decode Media", key="dec_button", 
                             disabled=(not uploaded_stego or not key_bytes_decode))

    if decode_button:
        if uploaded_stego and key_bytes_decode:
            try:
                if media_type == "Image":
                    stego_img_bgr = load_image_from_upload(uploaded_stego)
                    if stego_img_bgr is not None:
                        st.image(cv2.cvtColor(stego_img_bgr, cv2.COLOR_BGR2RGB), 
                                caption="Uploaded Stego Image", use_container_width=True)

                        with st.spinner(f"Decoding data using {stego_method}..."):
                            if stego_method == "LSB (Fast)":
                                extracted_encrypted_bytes = decode_lsb(stego_img_bgr)
                            else:  # DCT
                                extracted_encrypted_bytes = decode_dct(stego_img_bgr, quality_factor)

                elif media_type == "Audio":
                    temp_stego_path = save_uploaded_file(uploaded_stego, "temp")
                    
                    if temp_stego_path:
                        st.audio(uploaded_stego.getvalue(), format='audio/wav')
                        
                        with st.spinner("Decoding data from audio..."):
                            extracted_encrypted_bytes = decode_audio_lsb(temp_stego_path)
                        
                        # Cleanup
                        if os.path.exists(temp_stego_path):
                            os.remove(temp_stego_path)

                else:  # Video
                    temp_stego_path = save_uploaded_file(uploaded_stego, "temp")
                    
                    if temp_stego_path:
                        st.video(uploaded_stego.getvalue())
                        
                        with st.spinner("Decoding data from video... This may take several minutes."):
                            extracted_encrypted_bytes = decode_video_lsb(
                                temp_stego_path, 
                                embed_ratio=decode_embed_ratio
                            )
                        
                        # Cleanup
                        if os.path.exists(temp_stego_path):
                            os.remove(temp_stego_path)

                # Common decryption process
                if isinstance(extracted_encrypted_bytes, bytes):
                    st.info(f"Extracted {len(extracted_encrypted_bytes)} encrypted bytes.")
                    
                    with st.spinner("Decrypting data..."):
                        decrypted_original_bytes = decrypt_message(extracted_encrypted_bytes, key_bytes_decode)

                    if decrypted_original_bytes is not None:
                        st.success("Decryption Successful!")
                        st.subheader("Decoded Data:")

                        try:
                            decoded_text = decrypted_original_bytes.decode('utf-8')
                            st.text_area("Decoded Text:", decoded_text, height=200, key="decoded_text_area")
                        except UnicodeDecodeError:
                            st.warning("Decoded data is not valid UTF-8 text. Offering download instead.")
                            st.download_button(
                                label="Download Decoded File/Data",
                                data=decrypted_original_bytes,
                                file_name="decoded_secret_data",
                                mime="application/octet-stream",
                                key="download_decoded_button"
                            )
                    else:
                        st.error("Decryption Failed. Likely incorrect key or data corruption.")
                else:
                    st.error("Decoding Failed: Could not extract data.")

            except DecodingError as e:
                st.error(f"Decoding Failed: {e}")
            except (SteganographyError, ValueError, TypeError) as e:
                st.error(f"Decoding Failed: {e}")
                logging.error("Decoding process failed.", exc_info=True)
            except Exception as e:
                st.error(f"An unexpected error occurred during decoding: {e}")
                logging.error("Unexpected decoding error.", exc_info=True)

# --- ANALYSIS TAB ---
with tab3:
    st.header("📊 Steganography Analysis")
    
    st.subheader("Capacity Calculator")
    
    if media_type == "Image":
        width = st.number_input("Image Width (pixels):", min_value=1, value=1920)
        height = st.number_input("Image Height (pixels):", min_value=1, value=1080)
        channels = 3  # BGR
        
        if stego_method == "LSB (Fast)":
            max_capacity_bits = width * height * channels
            max_capacity_bytes = max_capacity_bits // 8
        else:  # DCT
            block_width = width // 8
            block_height = height // 8
            max_capacity_bits = block_width * block_height
            max_capacity_bytes = max_capacity_bits // 8
        
        st.info(f"**{stego_method} Capacity:** {max_capacity_bytes:,} bytes ({max_capacity_bits:,} bits)")
        
    elif media_type == "Audio":
        duration = st.number_input("Audio Duration (seconds):", min_value=0.1, value=10.0)
        sample_rate = st.selectbox("Sample Rate (Hz):", [44100, 22050, 16000, 8000])
        
        total_samples = int(duration * sample_rate)
        max_capacity_bits = total_samples
        max_capacity_bytes = max_capacity_bits // 8
        
        st.info(f"**Audio LSB Capacity:** {max_capacity_bytes:,} bytes ({max_capacity_bits:,} bits)")
    
    else:  # Video
        video_width = st.number_input("Video Width (pixels):", min_value=1, value=1920)
        video_height = st.number_input("Video Height (pixels):", min_value=1, value=1080)
        video_duration = st.number_input("Video Duration (seconds):", min_value=0.1, value=30.0)
        video_fps = st.selectbox("Video FPS:", [24, 25, 30, 60])
        analysis_embed_ratio = st.slider("Embed Ratio:", min_value=0.01, max_value=1.0, value=0.1)
        
        total_frames = int(video_duration * video_fps)
        frames_used = int(total_frames * analysis_embed_ratio)
        pixels_per_frame = video_width * video_height * 3  # RGB
        max_capacity_bits = pixels_per_frame * frames_used
        max_capacity_bytes = max_capacity_bits // 8
        
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"""
            **Video Specs:**
            - Resolution: {video_width}×{video_height}
            - Duration: {video_duration} seconds
            - FPS: {video_fps}
            - Total frames: {total_frames:,}
            """)
        
        with col2:
            st.info(f"""
            **Capacity:**
            - Frames used: {frames_used:,}
            - Capacity: {max_capacity_bytes/1024/1024:.2f} MB
            - Total: {max_capacity_bytes:,} bytes
            """)
    
    st.subheader("Method Comparison")
    
    comparison_data = {
        "Method": ["LSB Image", "DCT Image", "Audio LSB", "Video LSB"],
        "Speed": ["Fast", "Medium", "Fast", "Slow"],
        "Robustness": ["Low", "High", "Medium", "Low"],
        "Capacity": ["High", "Medium", "Very High", "Extremely High"],
        "Detectability": ["High", "Low", "Medium", "Medium"]
    }
    
    st.table(comparison_data)
    
    st.subheader("Security Notes")
    st.markdown("""
    **🔒 Encryption:** All methods use AES-256 encryption via Fernet for data security.
    
    **🕵️ Detectability:**
    - **LSB:** Easily detected by statistical analysis
    - **DCT:** More resistant to steganalysis
    - **Audio LSB:** Harder to detect due to audio noise
    - **Video LSB:** Detection depends on embed ratio and frame selection
    
    **🛡️ Robustness:**
    - **LSB:** Destroyed by any compression
    - **DCT:** Survives mild JPEG compression
    - **Audio LSB:** Survives some audio processing
    - **Video LSB:** Vulnerable to video re-encoding and compression
    
    **⚡ Performance:**
    - **Video processing** is computationally intensive
    - **Large file sizes** require significant storage and bandwidth
    - **Real-time encoding/decoding** not practical for long videos
    """)

# --- Footer ---
st.markdown("---")
st.markdown("""
**Advanced StegoTool v2.1** - Complete multimedia steganography with Image, Audio, and Video support.

⚠️ **Disclaimer:** This tool is for educational and research purposes. Use responsibly and in compliance with applicable laws.
""")

# Clean up temp directory on app restart
if os.path.exists("temp"):
    import shutil
    try:
        shutil.rmtree("temp")
    except:
        pass 
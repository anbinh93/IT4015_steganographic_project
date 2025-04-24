# app.py

import streamlit as st
import cv2
import numpy as np
import os
import io
import logging
import base64

# Import local modules
from steganography.lsb import encode_lsb, decode_lsb
from steganography.utils import (
    generate_key, encrypt_message, decrypt_message
)
from steganography.exceptions import CapacityError, EncodingError, DecodingError, SteganographyError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
OUTPUT_FORMAT = ".png" # Always save output as lossless PNG

# --- MODIFIED --- Allow JPEG/JPG uploads
ALLOWED_UPLOAD_TYPES = ['png', 'bmp', 'tiff', 'jpg', 'jpeg']

# --- Helper Functions ---
def load_image_from_upload(uploaded_file):
    # ... (no changes needed in this function itself) ...
    if uploaded_file is not None:
        try:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
            if img is None:
                 st.error("Could not decode image. Is the file format correct and supported?")
                 return None
            return img # Return BGR array for processing
        except Exception as e:
            st.error(f"Error loading image: {e}")
            logging.error(f"Failed to load/decode uploaded image: {e}", exc_info=True)
            return None
    return None


def get_image_download_bytes(img_array_bgr, format=OUTPUT_FORMAT):
    # ... (no changes needed in this function) ...
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
    # ... (no changes needed in this function - previous fix was correct) ...
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
st.set_page_config(page_title="StegoTool", layout="wide")
st.title("🖼️ StegoTool: Hide Secrets in Images")
st.caption("Uses LSB Steganography with AES Encryption")

tab1, tab2 = st.tabs(["🔒 Encode", "🔓 Decode"])

# --- ENCODE TAB ---
with tab1:
    st.header("Encode Message into Image")
    st.markdown("Upload a cover image and provide the secret data. **Lossless formats (PNG, BMP) are strongly recommended.**") # Added warning

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

    st.subheader("2. Upload Cover Image")
    # --- MODIFIED --- type now includes jpg/jpeg
    uploaded_cover_image = st.file_uploader(
        "Choose Cover Image (PNG, BMP recommended):",
        type=ALLOWED_UPLOAD_TYPES,
        key="enc_file_cover"
        )

    # --- ADDED WARNING for JPEG ---
    if uploaded_cover_image and uploaded_cover_image.type in ["image/jpeg", "image/jpg"]:
        st.warning("⚠️ **Warning:** Using JPEG/JPG as a cover image for LSB steganography is **highly discouraged**. "
                   "JPEG compression discards image data, which will likely corrupt or destroy the hidden message "
                   "if the image is ever re-saved or compressed again. The resulting stego image will be saved as PNG "
                   "to preserve the encoded data initially, but handle it with care.")

    st.subheader("3. Encode")
    encode_button = st.button("Encode Image", key="enc_button", disabled=(not uploaded_cover_image or not secret_data_bytes or not key_bytes_encode))

    if encode_button:
        if uploaded_cover_image and secret_data_bytes and key_bytes_encode:
            cover_img_bgr = load_image_from_upload(uploaded_cover_image)

            if cover_img_bgr is not None:
                # --- MODIFIED --- Fix deprecated use_column_width
                st.image(cv2.cvtColor(cover_img_bgr, cv2.COLOR_BGR2RGB), caption="Original Cover Image", use_container_width=True)

                try:
                    with st.spinner("Encrypting data..."):
                        encrypted_data = encrypt_message(secret_data_bytes, key_bytes_encode)
                    st.info(f"Data encrypted ({len(secret_data_bytes)} -> {len(encrypted_data)} bytes).")

                    with st.spinner("Encoding data into image... Please wait."):
                        stego_img_bgr = encode_lsb(cover_img_bgr, encrypted_data)

                    st.success("Encoding successful!")
                    # --- MODIFIED --- Fix deprecated use_column_width
                    st.image(cv2.cvtColor(stego_img_bgr, cv2.COLOR_BGR2RGB), caption="Stego (Encoded) Image (Saved as PNG)", use_container_width=True)

                    # Provide download link (always PNG)
                    download_bytes = get_image_download_bytes(stego_img_bgr, format=".png") # Explicitly PNG
                    if download_bytes:
                        st.download_button(
                            label="Download Stego Image (PNG)",
                            data=download_bytes,
                            file_name=f"stego_{os.path.splitext(uploaded_cover_image.name)[0]}{OUTPUT_FORMAT}",
                            mime="image/png"
                        )

                # ... (error handling remains the same) ...
                except CapacityError as e:
                    st.error(f"Encoding Failed: {e}")
                except (EncodingError, SteganographyError, ValueError, TypeError) as e:
                    st.error(f"Encoding Failed: {e}")
                    logging.error("Encoding process failed.", exc_info=True)
                except Exception as e:
                    st.error(f"An unexpected error occurred during encoding: {e}")
                    logging.error("Unexpected encoding error.", exc_info=True)


        elif not uploaded_cover_image:
            st.warning("Please upload a cover image.")
        elif not secret_data_bytes:
            st.warning("Please provide secret data (text or file).")
        elif not key_bytes_encode:
            st.warning("Encryption key is missing or invalid.")


# --- DECODE TAB ---
with tab2:
    st.header("Decode Message from Image")
    st.markdown("Upload a stego image and provide the correct encryption key.")

    key_bytes_decode = display_key_management(widget_key_prefix="decode")

    st.subheader("1. Upload Stego Image")
    # Allow decoding from any format, as LSB *might* survive if it was saved as PNG
    uploaded_stego_image = st.file_uploader(
        "Choose Stego Image:",
        type=ALLOWED_UPLOAD_TYPES, # Allow upload of original formats
        key="dec_file_stego"
        )

    st.subheader("2. Decode")
    decode_button = st.button("Decode Image", key="dec_button", disabled=(not uploaded_stego_image or not key_bytes_decode))

    if decode_button:
        if uploaded_stego_image and key_bytes_decode:
            stego_img_bgr = load_image_from_upload(uploaded_stego_image)

            if stego_img_bgr is not None:
                 # --- MODIFIED --- Fix deprecated use_column_width
                 st.image(cv2.cvtColor(stego_img_bgr, cv2.COLOR_BGR2RGB), caption="Uploaded Stego Image", use_container_width=True)

                 try:
                    with st.spinner("Decoding data from image..."):
                        # decode_lsb now correctly returns bytes or None/raises Error
                        extracted_encrypted_bytes = decode_lsb(stego_img_bgr)

                    # Check if bytes were returned before proceeding
                    if isinstance(extracted_encrypted_bytes, bytes): # Explicit check
                        st.info(f"Extracted {len(extracted_encrypted_bytes)} potentially encrypted bytes.")
                        with st.spinner("Decrypting data..."):
                             # Pass the extracted bytes directly to decrypt_message
                             decrypted_original_bytes = decrypt_message(extracted_encrypted_bytes, key_bytes_decode)

                        if decrypted_original_bytes is not None:
                             st.success("Decryption Successful!")
                             st.subheader("Decoded Data:")

                             # Attempt to display as text, provide download otherwise
                             try:
                                 # Decode the *decrypted* bytes as text
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
                    # This case now handles if decode_lsb explicitly returned None (less likely)
                    # or if extracted_encrypted_bytes was not bytes (shouldn't happen now)
                    # Most failures within decode_lsb should raise DecodingError now.
                    elif extracted_encrypted_bytes is None:
                         st.error("Decoding Failed: Could not extract data (decode_lsb returned None).")

                 except DecodingError as e:
                     st.error(f"Decoding Failed: {e}")
                 except (SteganographyError, ValueError, TypeError) as e:
                     st.error(f"Decoding Failed: {e}")
                     logging.error("Decoding process failed.", exc_info=True)
                 except Exception as e:
                     st.error(f"An unexpected error occurred during decoding: {e}")
                     logging.error("Unexpected decoding error.", exc_info=True)

        elif not uploaded_stego_image:
            st.warning("Please upload a stego image.")
        elif not key_bytes_decode:
             st.warning("Encryption key is missing or invalid.")


# --- Footer/Info ---
st.markdown("---")
# --- MODIFIED --- Added specific JPG warning to footer
st.markdown("""
**Important Notes:**
*   **Security:** This tool uses AES encryption, which is strong *if the key is kept secret*. However, basic LSB steganography itself is **not robust** and can be detected by steganalysis tools.
*   **Image Formats:** LSB is easily broken by image compression. **Always use lossless image formats like PNG or BMP as the cover image for reliable results.** While JPG upload is allowed, using it as a cover image is **highly likely to cause data loss** if the image is re-saved or compressed. The output stego image is always saved as PNG.
*   **Key Management:** The encryption key shown is stored temporarily in your browser session for this demo. For real applications, secure key exchange and storage are critical. **Do not share the key carelessly.**
*   **Update:** This tool is a demo and we are going to support encrypted messages and audio in soon"
""")
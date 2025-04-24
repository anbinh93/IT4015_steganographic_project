# Steganographic Data Hiding in Multimedia Files

## Group Members:
- **Nguyễn Bình An** – 20225591
- **Vũ Ngọc Đức** – 20225816
- **Lê Thị Quỳnh** – 20225917

## Project Overview:
This project demonstrates the use of steganography to hide sensitive information in various media files. Our approach follows a systematic process that starts with encrypting the data, embedding it in the least significant bits (LSBs) of an image, and then saving the modified image for later retrieval. The extraction process involves reversing these steps to retrieve the original data.

### Process Flow:
1. **Encrypt**: The data is first encrypted to ensure security.
2. **Add Delimiter**: A special delimiter is added to the encrypted data to mark the beginning and end of the hidden data.
3. **Convert to Bits**: The encrypted data is converted into binary format (bits).
4. **Hide Bits in Image LSBs**: The bits are then embedded into the LSBs of an image file.
5. **Save Image**: The image with hidden data is saved for transmission.

For extraction:
1. **Load Image**: The image containing the hidden data is loaded.
2. **Extract LSBs**: The least significant bits are extracted from the image.
3. **Find Delimiter**: The delimiter is used to identify where the hidden data starts and ends.
4. **Convert Bits to Bytes**: The bits before the delimiter are converted back into bytes.
5. **Decrypt**: The data is decrypted to restore the original message.
6. **Interpret/Display**: The final message is displayed or interpreted.

## Current Progress:
- **Demo Completed**: The data hiding in images has been successfully demonstrated.
- **Ongoing Development**: We are currently working on extending the system to hide data in audio and video files.

## Link to Report:
- **Ongoing**

## Instructions for Running the Application

1. **Clone the repository (or create the files):**
    ```bash
    git clone https://github.com/anbinh93/IT4015_steganographic_project.git
    cd steganography-app
    ```

2. **Create a virtual environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Running the Application

```bash
streamlit run app.py

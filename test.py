import os
import streamlit as st
from PyPDF2 import PdfReader
from gtts import gTTS
import pyttsx3
from pydub import AudioSegment
import docx
import tempfile
import shutil
import subprocess

# Add this at the top of your file, after the imports
AudioSegment.converter = r"C:\Users\Nipun Dhawan\Downloads\ffmpeg-2024-09-12-git-504c1ffcd8-full_build\ffmpeg-2024-09-12-git-504c1ffcd8-full_build\bin\ffmpeg.exe"  # Update this path

def extract_text(file):
    file_extension = os.path.splitext(file.name)[1].lower()

    if file_extension == '.pdf':
        reader = PdfReader(file)
        return " ".join(page.extract_text() for page in reader.pages)
    elif file_extension == '.docx':
        doc = docx.Document(file)
        return " ".join(paragraph.text for paragraph in doc.paragraphs)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def text_to_audiobook(text, output_path, language, speed_factor):
    st.write(f"Converting text to speech in {language}...")

    if language == 'en':
        # Use pyttsx3 for English
        engine = pyttsx3.init()
        engine.setProperty('rate', int(150 * speed_factor))  # Adjust base rate (150) as needed
        engine.save_to_file(text, output_path)
        engine.runAndWait()
    else:
        # Use gTTS for other languages
        tts = gTTS(text=text, lang=language, slow=(speed_factor < 1.0))
        tts.save(output_path)

def speed_up_audio(input_path, output_path, speed_factor=1.5):
    st.write(f"Adjusting audio speed by {speed_factor}x...")
    try:
        # Check if ffmpeg path is correct
        if not os.path.exists(AudioSegment.converter):
            st.error(f"FFmpeg not found at {AudioSegment.converter}")
            raise FileNotFoundError(f"FFmpeg not found at {AudioSegment.converter}")

        # Check if input file exists
        if not os.path.exists(input_path):
            st.error(f"Input file not found: {input_path}")
            raise FileNotFoundError(f"Input file not found: {input_path}")

        # Create a temporary file for the adjusted audio in the same directory as the output file
        temp_output_path = os.path.join(os.path.dirname(output_path), "temp_adjusted.mp3")

        # Use subprocess to run ffmpeg command
        command = [
            AudioSegment.converter,
            "-i", input_path,
            "-filter:a", f"atempo={speed_factor}",
            temp_output_path
        ]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"FFmpeg command failed with error: {result.stderr}")

        # Move the temporary file to the final output path
        if os.path.exists(output_path):
            os.remove(output_path)
        shutil.move(temp_output_path, output_path)

    except Exception as e:
        st.error(f"Error adjusting audio speed: {str(e)}")
        # If adjustment fails, just copy the original file
        if os.path.exists(output_path):
            os.remove(output_path)
        shutil.copy2(input_path, output_path)
        st.warning("Copied original file without speed adjustment.")

def main():
    st.title("PDF/DOCX to Audiobook Converter")

    # Define supported languages
    languages = {
        'English': 'en',
        'Hindi': 'hi',
        'Spanish': 'es',
        'French': 'fr',
        'German': 'de',
        # Add more languages as needed
    }

    uploaded_file = st.file_uploader("Choose a PDF or DOCX file", type=["pdf", "docx"])
    
    if uploaded_file is not None:
        st.success("File successfully uploaded!")

        # Language selection
        selected_language = st.selectbox(
            "Choose a language",
            options=list(languages.keys()),
            format_func=lambda x: x
        )
        selected_language_code = languages[selected_language]

        # Speed factor selection
        speed_factor = st.slider("Choose speed factor", min_value=0.5, max_value=3.0, value=1.0, step=0.1)

        if st.button("Convert to Audiobook"):
            try:
                with st.spinner("Extracting text from file..."):
                    text = extract_text(uploaded_file)

                # Use a temporary file for the initial output
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                    temp_output_path = temp_file.name

                with st.spinner("Converting text to audiobook..."):
                    text_to_audiobook(text, temp_output_path, selected_language_code, speed_factor)

                final_output_path = "output.mp3"
                if speed_factor != 1.0:
                    with st.spinner("Adjusting audio speed..."):
                        speed_up_audio(temp_output_path, final_output_path, speed_factor)
                else:
                    shutil.move(temp_output_path, final_output_path)

                st.success(f"Audiobook created successfully!")
                st.audio(final_output_path)

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
            finally:
                # Clean up temporary file if it exists
                if 'temp_output_path' in locals() and os.path.exists(temp_output_path):
                    os.remove(temp_output_path)

if __name__ == "__main__":
    main()
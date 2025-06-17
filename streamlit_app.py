import streamlit as st
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import tempfile
import re
import os

st.set_page_config(page_title="MCQ Extractor Tool", layout="wide")
st.title("📄 MCQ PDF Extractor with Answer Formatter")
st.write("Upload your question paper PDF and extract all questions and answers in a clean format.")

uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

if uploaded_file:
    with st.spinner("Processing PDF..."):
        # Convert PDF to images
        images = convert_from_bytes(uploaded_file.read())
        
        questions = []
        answers = []
        question_counter = 1

        for page_num, image in enumerate(images):
            image = image.convert("L")
            try:
                text = pytesseract.image_to_string(image, lang='eng')
            except Exception as e:
                st.error(f"Error during OCR processing on page {page_num + 1}: {e}")
                text = "" # Continue with empty text for this page
            # Basic chunking based on patterns like "Q." or numbered questions
            chunks = re.split(r'\n(?=Q(?:ues(?:tion)?)?[\s\.\d])', text)
            for chunk in chunks:
                if chunk.strip():
                    # Clean and structure the question
                    q_match = re.search(r'(Q(?:ues(?:tion)?)?[\s\.\d]*.*?)(\s*Options.*?)?((?:1\..*?\n2\..*?\n3\..*?\n4\..*?))(.*)', chunk, re.DOTALL)
                    if q_match:
                        try:
                            question_text = q_match.group(1).strip()
                            options_block = q_match.group(3).strip()

                            # Detect the green check mark (✓) in options (simulate by matching it)
                            correct_option = None
                            options = []
                            for line in options_block.splitlines():
                                original_line_for_number_extraction = line # Keep original for number extraction

                                if ('✓' in line or '✔' in line) and correct_option is None: # Process only the first checkmark
                                    num_match = re.match(r'\s*(\d+)', original_line_for_number_extraction)
                                    if num_match:
                                        try:
                                            correct_option = int(num_match.group(1))
                                        except ValueError:
                                            st.warning(f"Could not parse option number for answer from: '{original_line_for_number_extraction[:30]}...'")
                                    else:
                                        st.warning(f"Found checkmark but could not determine option number from start of line: '{original_line_for_number_extraction[:30]}...'")

                                # Always clean the line for options list
                                cleaned_line = line.replace('✓', '').replace('✔', '').strip()
                                options.append(cleaned_line)

                            # Format question block
                            formatted = f"Q.{question_counter} {question_text}\n\nOptions"
                            for opt in options:
                                formatted += f"\n{opt}"
                            questions.append(formatted)

                            # Store answer
                            answers.append(f"{question_counter}. {correct_option if correct_option else '-'}")
                            question_counter += 1
                        except Exception as e:
                            st.error(f"Error parsing matched question block: '{chunk[:100].strip()}...'. Error: {e}")
                    else:
                        # Add this line to log when a chunk doesn't match the regex
                        if chunk.strip(): # Avoid logging empty chunks
                            st.warning(f"Could not parse a potential question block: '{chunk[:100].strip()}...'")

        # Output construction
        output_text = "\n\n".join(questions)

        # Add answers
        output_text += "\n\nAnswers\n"
        # Group answers 3 per row
        grouped_answers = [answers[i:i+3] for i in range(0, len(answers), 3)]
        for group in grouped_answers:
            output_text += "     ".join(group) + "\n"

        # Downloadable output
        st.success("Done! Preview below:")
        st.text_area("Formatted Output", output_text, height=500)

        # File export
        f_path = None  # Initialize f_path
        try:
            with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix=".txt") as f:
                f.write(output_text)
                f_path = f.name

            # It's important that the download button is generated *before* the file is deleted.
            # Streamlit's download button likely needs the file to exist at the moment it prepares the download.
            # One common pattern is to read the file bytes then offer them directly.

            # Let's read the bytes first, then offer them. This avoids holding the temp file open or relying on its path
            # for the duration of the download button's existence if Streamlit caches it.

            with open(f_path, "rb") as file_bytes_to_download:
                st.download_button(
                    label="📥 Download Output as .txt",
                    data=file_bytes_to_download, # Pass bytes directly
                    file_name="mcq_output.txt",
                    mime="text/plain" # Explicitly set mime type for .txt
                )
        except Exception as e:
            st.error(f"Error during file preparation for download: {e}")
        finally:
            if f_path and os.path.exists(f_path):
                try:
                    os.remove(f_path)
                except Exception as e:
                    st.warning(f"Could not delete temporary file {f_path}: {e}")

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
            text = pytesseract.image_to_string(image)
            # Basic chunking based on patterns like "Q." or numbered questions
            chunks = re.split(r'\n(?=Q[\.\d])', text)
            for chunk in chunks:
                if chunk.strip():
                    # Clean and structure the question
                    q_match = re.search(r'(Q[\.\d]+.*?)(Options.*?)((?:1\..*?\n2\..*?\n3\..*?\n4\..*?))(.*)', chunk, re.DOTALL)
                    if q_match:
                        question_text = q_match.group(1).strip()
                        options_block = q_match.group(3).strip()

                        # Detect the green check mark (✓) in options (simulate by matching it)
                        correct_option = None
                        options = []
                        for line in options_block.splitlines():
                            if '✓' in line or '✔' in line:
                                correct_option = int(line[0])
                                line = line.replace('✓', '').replace('✔', '').strip()
                            options.append(line)

                        # Format question block
                        formatted = f"Q.{question_counter} {question_text}\n\nOptions"
                        for opt in options:
                            formatted += f"\n{opt}"
                        questions.append(formatted)

                        # Store answer
                        answers.append(f"{question_counter}. {correct_option if correct_option else '-'}")
                        question_counter += 1

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
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix=".txt") as f:
            f.write(output_text)
            f_path = f.name

        with open(f_path, "rb") as file:
            st.download_button("📥 Download Output as .txt", file, file_name="mcq_output.txt")

        os.remove(f_path)

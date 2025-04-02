import os
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF file.
    """
    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error processing PDF {pdf_path}: {str(e)}")
        return None

def process_pdf_directory(directory_path):
    """
    Process all PDF files in a directory and return their contents.
    """
    pdf_contents = []
    for filename in os.listdir(directory_path):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(directory_path, filename)
            text = extract_text_from_pdf(pdf_path)
            if text:
                pdf_contents.append({
                    'filename': filename,
                    'content': text
                })
    return pdf_contents 
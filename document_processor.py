import os
from docx import Document
import PyPDF2
from typing import Optional, Dict, List
import win32com.client
import pythoncom
import gc
from audio_processor import extract_text_from_audio
import tempfile
import shutil

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file."""
    try:
        # Convert to absolute path
        abs_path = os.path.abspath(file_path)
        print(f"Processing DOCX file: {abs_path}")
        print(f"File exists: {os.path.exists(abs_path)}")
        
        # Create a temporary copy to avoid file access issues
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, os.path.basename(abs_path))
        shutil.copy2(abs_path, temp_path)
        
        doc = Document(temp_path)
        text = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():  # Only add non-empty paragraphs
                text.append(paragraph.text)
        
        result = '\n'.join(text)
        print(f"Successfully extracted {len(text)} paragraphs")
        
        # Clean up
        shutil.rmtree(temp_dir)
        return result
    except Exception as e:
        print(f"Error processing DOCX file {file_path}: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Clean up temp directory if it exists
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        return None

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    try:
        # Convert to absolute path
        abs_path = os.path.abspath(file_path)
        print(f"Processing PDF file: {abs_path}")
        
        # Get file size in MB
        file_size_mb = os.path.getsize(abs_path) / (1024 * 1024)
        print(f"PDF file size: {file_size_mb:.2f} MB")
        
        # Create a temporary copy to avoid file access issues
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, os.path.basename(abs_path))
        shutil.copy2(abs_path, temp_path)
        
        with open(temp_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = []
            
            # Process pages
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():  # Only add non-empty pages
                        text.append(page_text)
                    
                    # Force garbage collection every 10 pages for large files
                    if file_size_mb > 50 and page_num % 10 == 0:
                        gc.collect()
                        
                except Exception as e:
                    print(f"Error processing page {page_num} of {abs_path}: {str(e)}")
                    continue
        
        # Clean up
        shutil.rmtree(temp_dir)
        return '\n'.join(text)
    except Exception as e:
        print(f"Error processing PDF file {file_path}: {str(e)}")
        # Clean up temp directory if it exists
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
        return None

def extract_text_from_doc(doc_path):
    """Extract text from a DOC file by converting to DOCX first."""
    try:
        # Convert to absolute path
        abs_path = os.path.abspath(doc_path)
        print(f"Processing DOC file: {abs_path}")
        
        # Create a temporary directory for conversion
        temp_dir = tempfile.mkdtemp()
        temp_docx = os.path.join(temp_dir, os.path.basename(doc_path).replace('.doc', '.docx'))
        
        # Convert DOC to DOCX
        if convert_doc_to_docx(abs_path, temp_docx):
            try:
                # Extract text from the converted DOCX
                content = extract_text_from_docx(temp_docx)
                return content
            except Exception as e:
                print(f"Error processing converted DOCX file: {str(e)}")
        return None
    except Exception as e:
        print(f"Error processing DOC file {doc_path}: {str(e)}")
        return None
    finally:
        # Clean up temp directory
        if 'temp_dir' in locals():
            try:
                shutil.rmtree(temp_dir)
            except:
                pass

def convert_doc_to_docx(doc_path, output_path):
    """Convert DOC to DOCX using Word COM automation."""
    word = None
    try:
        pythoncom.CoInitialize()
        word = win32com.client.Dispatch('Word.Application')
        word.Visible = False  # Run Word in background
        
        # Create a unique temporary file name
        doc = word.Documents.Open(doc_path)
        doc.SaveAs2(output_path, FileFormat=16)  # 16 = docx format
        doc.Close()
        return True
    except Exception as e:
        print(f"Error converting DOC to DOCX {doc_path}: {str(e)}")
        return False
    finally:
        try:
            if word:
                word.Quit()
            pythoncom.CoUninitialize()
        except Exception as e:
            print(f"Error cleaning up Word COM: {str(e)}")

def extract_text_from_txt(file_path):
    """Extract text from a TXT file."""
    try:
        # Convert to absolute path
        abs_path = os.path.abspath(file_path)
        print(f"Processing TXT file: {abs_path}")
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'cp1252', 'ascii']
        for encoding in encodings:
            try:
                with open(abs_path, 'r', encoding=encoding) as file:
                    content = file.read()
                    if content.strip():  # Only return if content is not empty
                        print(f"Successfully read TXT file with {encoding} encoding")
                        return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"Error reading TXT file with {encoding} encoding: {str(e)}")
                continue
        
        print("Failed to read TXT file with any encoding")
        return None
    except Exception as e:
        print(f"Error processing TXT file {file_path}: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return None

def process_document_directory(directory_path):
    """Process all supported documents in the specified directory."""
    processed_docs = []
    
    # Get all files in the directory
    try:
        files = [f for f in os.listdir(directory_path) if os.path.isfile(os.path.join(directory_path, f))]
        print(f"Found {len(files)} files in directory")
        
        # Sort files by size to process smaller files first
        files.sort(key=lambda x: os.path.getsize(os.path.join(directory_path, x)))
        
        for filename in files:
            try:
                file_path = os.path.join(directory_path, filename)
                file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                print(f"Processing {filename} ({file_size_mb:.2f} MB)")
                
                content = None
                # Process based on file extension
                if filename.lower().endswith('.pdf'):
                    content = extract_text_from_pdf(file_path)
                elif filename.lower().endswith('.docx'):
                    content = extract_text_from_docx(file_path)
                elif filename.lower().endswith('.doc'):
                    content = extract_text_from_doc(file_path)
                elif filename.lower().endswith('.txt'):
                    content = extract_text_from_txt(file_path)
                elif filename.lower().endswith(('.wav', '.mp3')):
                    content = extract_text_from_audio(file_path)
                
                if content and content.strip():  # Only add if content is not empty
                    processed_docs.append({
                        'filename': filename,
                        'content': content,
                        'preview': content[:1000] + "..." if len(content) > 1000 else content
                    })
                    print(f"Successfully processed {filename}")
                else:
                    print(f"Failed to extract content from {filename}")
                
                # Force garbage collection for large files
                if file_size_mb > 50:
                    gc.collect()
                    
            except Exception as e:
                print(f"Error processing file {filename}: {str(e)}")
                continue
                
    except Exception as e:
        print(f"Error accessing directory {directory_path}: {str(e)}")
        return []
        
    print(f"Successfully processed {len(processed_docs)} out of {len(files)} files")
    return processed_docs 
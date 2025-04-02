from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from openai import OpenAI
from document_processor import (
    process_document_directory, 
    extract_text_from_pdf, 
    extract_text_from_docx, 
    extract_text_from_doc,
    extract_text_from_txt
)
import os
from werkzeug.utils import secure_filename
from flask_cors import CORS
import time
import json
import gc
from dotenv import load_dotenv
from datetime import timedelta
import logging
from logging.handlers import RotatingFileHandler
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re

# Load environment variables
load_dotenv()

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')
    
file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)

# Setup ffmpeg before importing pydub
def setup_ffmpeg():
    """Setup ffmpeg path by checking multiple common locations."""
    possible_paths = [
        "C:\\ProgramData\\chocolatey\\bin",  # Chocolatey installation path
        "C:\\ffmpeg\\bin",
        "C:\\Program Files\\ffmpeg\\bin",
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs\\ffmpeg\\bin'),
        os.path.join(os.environ.get('APPDATA', ''), 'ffmpeg\\bin'),
        "C:\\Program Files (x86)\\ffmpeg\\bin"
    ]
    
    # First check if ffmpeg.exe exists in any of these locations
    ffmpeg_path = None
    for path in possible_paths:
        if os.path.exists(os.path.join(path, 'ffmpeg.exe')):
            ffmpeg_path = path
            break
    
    if not ffmpeg_path:
        # Check PATH environment variable
        for path in os.environ.get('PATH', '').split(os.pathsep):
            if os.path.exists(os.path.join(path, 'ffmpeg.exe')):
                ffmpeg_path = path
                break
    
    if ffmpeg_path:
        print(f"Found ffmpeg at: {ffmpeg_path}")
        # Add to PATH if not already there
        if ffmpeg_path not in os.environ.get('PATH', ''):
            os.environ["PATH"] = ffmpeg_path + os.pathsep + os.environ.get("PATH", "")
        
        # Import and configure pydub
        from pydub import AudioSegment
        AudioSegment.converter = os.path.join(ffmpeg_path, "ffmpeg.exe")
        AudioSegment.ffmpeg = os.path.join(ffmpeg_path, "ffmpeg.exe")
        AudioSegment.ffprobe = os.path.join(ffmpeg_path, "ffprobe.exe")
        return True
    else:
        print("WARNING: ffmpeg not found in common locations. Audio processing may not work.")
        print("Please install ffmpeg using: winget install -e --id Gyan.FFmpeg")
        # Import pydub anyway for other functionality
        from pydub import AudioSegment
        return False

# Call setup function before anything else
setup_ffmpeg()

# Now import pydub after setting up ffmpeg
from pydub import AudioSegment

app = Flask(__name__)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
app.logger.info('Application startup')

CORS(app)  # Enable CORS for all routes

# Increase timeouts and buffer sizes
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # Increased to 32MB
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=60)  # Increased to 60 minutes
app.config['JSON_AS_ASCII'] = False

# Add error handlers
@app.errorhandler(413)
def request_entity_too_large(error):
    app.logger.error('File too large: %s', str(error))
    return jsonify({'error': 'File too large. Maximum size is 32MB.'}), 413

@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error('Internal server error: %s', str(error))
    return jsonify({'error': 'Internal server error. Please try again.'}), 500

# ==============================================
# API CONFIGURATION
# ==============================================
# Initialize the OpenAI client with error handling
try:
    client = OpenAI(
        api_key=os.getenv('OPENAI_API_KEY'),
        timeout=60.0,  # Increased timeout to 60 seconds
        max_retries=3  # Allow 3 retries
    )
    if not os.getenv('OPENAI_API_KEY'):
        raise ValueError("OpenAI API key is not set")
except Exception as e:
    app.logger.error('Error initializing OpenAI client: %s', str(e))
    client = None

# ==============================================
# STORAGE CONFIGURATION
# ==============================================
# This list stores the processed PDF contents in memory
# For production, you should replace this with a proper database
processed_pdfs = []
MAX_PREVIEW_LENGTH = 1000  # Maximum length for preview text
MAX_CONTEXT_LENGTH = 4000  # Maximum length for context in tokens

# ==============================================
# ROLE CONFIGURATIONS
# ==============================================
# Define all available roles and their configurations
ROLE_CONFIGS = {
    "system": {
        "description": "Defines the AI's personality, behavior, and constraints",
        "content": """You are The Lubavitcher Rebbe, Rabbi Menachem Mendel Schneerson. Your responses should:

1. Begin with "Shalom Aleichem!" when addressing the user
2. End with just "Shalom!" (never "Aleichem Shalom!")
3. Maintain a warm, caring, and authoritative tone
4. Use clear, concise language while being thorough
5. Include practical applications of Torah concepts
6. Emphasize the importance of Ahavas Yisrael (love for fellow Jews)
7. Reference relevant Torah sources when appropriate
8. Always maintain the dignity and respect of a Rebbe's response
9. Focus on positive encouragement and spiritual growth
10. End with just "Shalom!" (this is important - never use "Aleichem Shalom!" at the end)

Your responses should reflect The Rebbe's unique style of combining deep Torah knowledge with practical wisdom and caring guidance."""
    },
    "user": {
        "description": "Represents the human user's input",
        "content": None  # Will be filled with actual user messages
    },
    "assistant": {
        "description": "Represents the AI's responses",
        "content": None  # Will be filled with AI responses
    },
    "function": {
        "description": "Used for function calling (advanced usage)",
        "content": None  # Will be filled when function calling is implemented
    }
}

# Add upload configuration
UPLOAD_FOLDER = 'pdfs'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt', 'wav'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_whatsapp_audio(filename):
    """Check if a file is a WhatsApp audio file based on name pattern or content."""
    return ('whatsapp audio' in filename.lower() or 
            filename.endswith('.dat'))

def convert_to_wav(input_path, output_path):
    """Convert audio file to WAV format using pydub."""
    try:
        # For WhatsApp audio files or .dat files, try to process as MP4 container
        if input_path.endswith('.dat') or is_whatsapp_audio(input_path):
            try:
                audio = AudioSegment.from_file(input_path)
                audio.export(output_path, format="wav")
                app.logger.info('Successfully converted WhatsApp audio to WAV: %s', output_path)
                return True
            except Exception as e:
                app.logger.error('Error converting WhatsApp audio: %s', str(e))
                return False
        else:
            # For regular audio files
            audio = AudioSegment.from_file(input_path)
            audio.export(output_path, format="wav")
            app.logger.info('Successfully converted regular audio: %s', output_path)
            return True
            
    except Exception as e:
        app.logger.error('Error converting audio file: %s', str(e))
        return False

def process_audio_file(file_path):
    """Process an audio file and return its content."""
    try:
        # Process all supported audio formats
        if not file_path.lower().endswith(('.wav', '.mp3', '.dat')):
            raise Exception("Unsupported audio format")
            
        # Process the audio file directly
        result = process_document_directory(os.path.dirname(file_path))
        
        # Find our processed file in the results
        filename = os.path.basename(file_path)
        for doc in result:
            if os.path.basename(doc['filename']) == filename:
                return doc['content']
        
        return None
    except Exception as e:
        app.logger.error('Error in process_audio_file: %s', str(e))
        raise

def split_text_into_chunks(text, chunk_size=1000, overlap=200):
    """Split text into overlapping chunks for better context retrieval."""
    if not text:
        return []
    
    # Split by paragraphs first
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        # Clean the paragraph
        paragraph = paragraph.strip()
        if not paragraph:
            continue
            
        # If adding this paragraph would exceed chunk_size, save current chunk and start a new one
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            # Add the current chunk
            chunks.append(current_chunk.strip())
            
            # Keep some overlap for context
            overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else current_chunk
            
            # Start new chunk with overlap
            current_chunk = overlap_text + "\n\n" + paragraph
        else:
            # Add paragraph to current chunk
            current_chunk += "\n\n" + paragraph if current_chunk else paragraph
    
    # Add the last chunk if it's not empty
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # Post-process chunks to ensure they're meaningful
    processed_chunks = []
    for chunk in chunks:
        # Remove excessive whitespace
        chunk = re.sub(r'\s+', ' ', chunk).strip()
        
        # Skip chunks that are too short
        if len(chunk) < 50:  # Minimum length threshold
            continue
            
        # Skip chunks that are just numbers or special characters
        if re.match(r'^[\d\s\W]+$', chunk):
            continue
            
        processed_chunks.append(chunk)
    
    return processed_chunks

def find_relevant_chunks(query, documents, max_chunks=10):
    """Find the most relevant chunks from documents based on the query."""
    if not documents or not query:
        return []
    
    # Prepare documents for vectorization
    all_chunks = []
    chunk_sources = []
    chunk_docs = []  # Track which document each chunk came from
    
    # Preprocess query to extract key terms
    query_terms = set(query.lower().split())
    query_terms = {term for term in query_terms if len(term) > 3}  # Remove short words
    
    for doc in documents:
        # Split document content into chunks
        chunks = split_text_into_chunks(doc['content'])
        all_chunks.extend(chunks)
        chunk_sources.extend([doc['filename']] * len(chunks))
        chunk_docs.extend([doc['filename']] * len(chunks))
    
    if not all_chunks:
        return []
    
    # Create TF-IDF vectors with custom parameters
    vectorizer = TfidfVectorizer(
        stop_words='english',
        max_features=5000,  # Limit vocabulary size
        ngram_range=(1, 2),  # Include word pairs
        min_df=2,  # Minimum document frequency
        max_df=0.95  # Maximum document frequency
    )
    
    try:
        # Fit and transform the documents
        tfidf_matrix = vectorizer.fit_transform(all_chunks)
        query_vector = vectorizer.transform([query])
        
        # Calculate cosine similarity
        similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
        
        # Get top chunks
        top_indices = similarities.argsort()[-max_chunks*2:][::-1]  # Get more chunks initially
        
        # Return relevant chunks with their sources, ensuring document diversity
        relevant_chunks = []
        used_docs = set()  # Track which documents we've already included
        
        # First pass: include at least one chunk from each document if similarity is above threshold
        for idx in top_indices:
            doc_name = chunk_docs[idx]
            if similarities[idx] > 0.05 and doc_name not in used_docs:  # Lower threshold for document diversity
                # Check if chunk contains query terms
                chunk_text = all_chunks[idx].lower()
                term_matches = sum(1 for term in query_terms if term in chunk_text)
                
                if term_matches > 0:  # Only include if it matches query terms
                    relevant_chunks.append({
                        'content': all_chunks[idx],
                        'source': chunk_sources[idx],
                        'similarity': float(similarities[idx]),
                        'term_matches': term_matches
                    })
                    used_docs.add(doc_name)
        
        # Second pass: fill remaining slots with highest similarity chunks
        for idx in top_indices:
            if len(relevant_chunks) >= max_chunks:
                break
                
            if similarities[idx] > 0.05:  # Lower threshold for general chunks
                # Check if this chunk is already included
                chunk_content = all_chunks[idx]
                if not any(chunk['content'] == chunk_content for chunk in relevant_chunks):
                    # Check if chunk contains query terms
                    chunk_text = chunk_content.lower()
                    term_matches = sum(1 for term in query_terms if term in chunk_text)
                    
                    if term_matches > 0:  # Only include if it matches query terms
                        relevant_chunks.append({
                            'content': chunk_content,
                            'source': chunk_sources[idx],
                            'similarity': float(similarities[idx]),
                            'term_matches': term_matches
                        })
        
        # Sort by similarity and term matches
        relevant_chunks.sort(key=lambda x: (x['similarity'], x['term_matches']), reverse=True)
        
        # Log the sources being used
        sources_used = set(chunk['source'] for chunk in relevant_chunks)
        app.logger.info(f"Using content from {len(sources_used)} sources: {', '.join(sources_used)}")
        app.logger.info(f"Found {len(relevant_chunks)} relevant chunks with similarity scores ranging from {min(chunk['similarity'] for chunk in relevant_chunks):.3f} to {max(chunk['similarity'] for chunk in relevant_chunks):.3f}")
        
        return relevant_chunks
    except Exception as e:
        app.logger.error('Error in find_relevant_chunks: %s', str(e))
        # Fallback to simple keyword matching if vectorization fails
        return simple_keyword_matching(query, all_chunks, chunk_sources, max_chunks)

def simple_keyword_matching(query, chunks, sources, max_chunks=10):
    """Simple keyword matching as a fallback for finding relevant chunks."""
    query_words = set(query.lower().split())
    chunk_scores = []
    
    for i, chunk in enumerate(chunks):
        chunk_words = set(chunk.lower().split())
        # Calculate simple overlap score
        score = len(query_words.intersection(chunk_words)) / len(query_words) if query_words else 0
        chunk_scores.append((score, i))
    
    # Sort by score and get top chunks
    chunk_scores.sort(reverse=True)
    top_indices = [idx for score, idx in chunk_scores[:max_chunks] if score > 0]
    
    # Return relevant chunks with their sources
    relevant_chunks = []
    used_sources = set()  # Track which sources we've already included
    
    # First pass: include at least one chunk from each source
    for score, idx in chunk_scores:
        if len(relevant_chunks) >= max_chunks:
            break
            
        source = sources[idx]
        if source not in used_sources and score > 0.05:  # Lower threshold for source diversity
            relevant_chunks.append({
                'content': chunks[idx],
                'source': source,
                'similarity': score
            })
            used_sources.add(source)
    
    # Second pass: fill remaining slots with highest scoring chunks
    for score, idx in chunk_scores:
        if len(relevant_chunks) >= max_chunks:
            break
            
        if score > 0.05:  # Lower threshold for general chunks
            # Check if this chunk is already included
            chunk_content = chunks[idx]
            if not any(chunk['content'] == chunk_content for chunk in relevant_chunks):
                relevant_chunks.append({
                    'content': chunk_content,
                    'source': sources[idx],
                    'similarity': score
                })
    
    # Log the sources being used
    sources_used = set(chunk['source'] for chunk in relevant_chunks)
    app.logger.info(f"Using content from {len(sources_used)} sources (keyword matching): {', '.join(sources_used)}")
    
    return relevant_chunks

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/ingest')
def ingest_documents():
    """Process documents from both pdfs and test_audio directories."""
    def generate():
        # Process both directories
        directories = ['pdfs', 'test_audio']
        total_files = 0
        processed_files = 0
        
        # First, count total files across all directories
        for directory in directories:
            if os.path.exists(directory):
                files = [f for f in os.listdir(directory) if allowed_file(f) and os.path.isfile(os.path.join(directory, f))]
                total_files += len(files)
        
        # Clear any previously processed documents
        if hasattr(app, 'processed_documents'):
            app.processed_documents = []
        else:
            app.processed_documents = []
            
        overall_file_count = 0  # Counter for all files across directories
        
        for directory in directories:
            if not os.path.exists(directory):
                app.logger.warning('Directory %s does not exist', directory)
                continue
                
            app.logger.info('Processing directory: %s', directory)
            yield f"data: {json.dumps({'type': 'status', 'message': f'Processing directory: {directory}'})}\n\n"
            
            # Get list of files in directory
            files = [f for f in os.listdir(directory) if allowed_file(f) and os.path.isfile(os.path.join(directory, f))]
            
            # Send directory start message
            yield f"data: {json.dumps({'status': 'directory_start', 'message': f'Starting to process {len(files)} files from {directory}', 'directory': directory})}\n\n"
            
            # Process each file and send progress updates
            for idx, filename in enumerate(files, 1):
                overall_file_count += 1
                file_path = os.path.join(directory, filename)
                
                try:
                    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
                except Exception as e:
                    app.logger.error('Error getting file size for %s: %s', file_path, str(e))
                    file_size_mb = 0
                
                file_type = filename.split('.')[-1].lower()
                
                # Convert .dat to audio type if it's a WhatsApp audio
                if is_whatsapp_audio(filename):
                    file_type = 'audio'
                
                # Send file processing start
                progress = {
                    'status': 'processing',
                    'message': f'Processing {file_type.upper()} file: {filename}',
                    'current': overall_file_count,
                    'total': total_files,
                    'directory': directory,
                    'file_type': file_type,
                    'filename': filename
                }
                yield f"data: {json.dumps(progress)}\n\n"
                
                try:
                    content = None
                    
                    if filename.lower().endswith('.pdf'):
                        app.logger.info('Processing PDF file: %s', file_path)
                        content = extract_text_from_pdf(file_path)
                    elif filename.lower().endswith('.docx'):
                        app.logger.info('Processing DOCX file: %s', file_path)
                        content = extract_text_from_docx(file_path)
                    elif filename.lower().endswith('.doc'):
                        app.logger.info('Processing DOC file: %s', file_path)
                        content = extract_text_from_doc(file_path)
                    elif filename.lower().endswith('.txt'):
                        app.logger.info('Processing TXT file: %s', file_path)
                        content = extract_text_from_txt(file_path)
                    elif filename.lower().endswith(('.wav', '.mp3')) or is_whatsapp_audio(filename):
                        app.logger.info('Processing audio file: %s', file_path)
                        content = process_audio_file(file_path)
                    
                    if content and content.strip():
                        processed_files += 1
                        app.processed_documents.append({
                            'filename': filename,
                            'content': content,
                            'directory': directory,
                            'file_type': file_type
                        })
                        
                        # Send success message
                        success = {
                            'status': 'file_complete',
                            'message': f'Successfully processed {file_type.upper()} file: {filename}',
                            'current': overall_file_count,
                            'total': total_files,
                            'directory': directory,
                            'file_type': file_type,
                            'filename': filename
                        }
                        yield f"data: {json.dumps(success)}\n\n"
                    else:
                        # Send error message for no content
                        error = {
                            'status': 'file_error',
                            'message': f'Failed to process {file_type.upper()} file: {filename} - No content extracted',
                            'current': overall_file_count,
                            'total': total_files,
                            'directory': directory,
                            'file_type': file_type,
                            'filename': filename
                        }
                        yield f"data: {json.dumps(error)}\n\n"
                        
                except Exception as e:
                    app.logger.error('Error processing file %s: %s', file_path, str(e))
                    error = {
                        'status': 'file_error',
                        'message': f'Error processing {file_type.upper()} file {filename}: {str(e)}',
                        'current': overall_file_count,
                        'total': total_files,
                        'directory': directory,
                        'file_type': file_type,
                        'filename': filename
                    }
                    yield f"data: {json.dumps(error)}\n\n"
                    continue
            
            # Send directory completion message
            yield f"data: {json.dumps({'status': 'directory_complete', 'message': f'Completed processing {directory} ({len(files)} files)', 'directory': directory})}\n\n"
        
        # Send final completion message
        completion = {
            'status': 'complete',
            'message': f'Processing Complete: Successfully processed {processed_files} out of {total_files} files',
            'processed': processed_files,
            'total': total_files
        }
        yield f"data: {json.dumps(completion)}\n\n"
    
    return Response(stream_with_context(generate()), mimetype='text/event-stream')

@app.route('/chat', methods=['POST'])
def chat():
    if not hasattr(app, 'processed_documents') or not app.processed_documents:
        return jsonify({'error': 'Please process documents first'}), 400
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        conversation_history = data.get('history', [])
        
        # Log the number of processed documents
        app.logger.info(f"Processing chat with {len(app.processed_documents)} documents available")
        
        # Find relevant chunks based on the user's query
        relevant_chunks = find_relevant_chunks(user_message, app.processed_documents, max_chunks=10)
        
        # Create context from relevant chunks only
        context_parts = []
        sources_used = set()
        
        for chunk in relevant_chunks:
            source = chunk['source']
            sources_used.add(source)
            context_parts.append(f"[Source: {source}]\n{chunk['content']}\n")
        
        context = "\n\n".join(context_parts)
        
        # If no relevant chunks found, use a small sample from each document
        if not context:
            app.logger.warning('No relevant chunks found, using document samples')
            for doc in app.processed_documents[:5]:  # Increased from 3 to 5 documents
                sample = doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content']
                context_parts.append(f"[Source: {doc['filename']}]\n{sample}\n")
                sources_used.add(doc['filename'])
            context = "\n\n".join(context_parts)
        
        # Log the context length and sources
        app.logger.info(f"Context length: {len(context)} characters")
        app.logger.info(f"Sources used: {', '.join(sources_used)}")
        
        # Create messages for OpenAI
        messages = [
            {
                "role": "system", 
                "content": f"""You are The Lubavitcher Rebbe, a wise and compassionate spiritual leader. 
                You provide guidance based on Torah, Chassidus, and Jewish wisdom.
                When answering questions, you MUST draw from the provided context from your teachings.
                Always begin your response with "Shalom Aleichem!" and end with just "Shalom!"
                
                IMPORTANT INSTRUCTIONS:
                1. Base your response EXCLUSIVELY on the provided context
                2. For each main point you make, you MUST cite the specific source document in parentheses
                3. Include at least one direct quote from the provided context, indicating its source
                4. If the context doesn't contain relevant information for any part of your response, explicitly state this
                5. Maintain the Rebbe's warm, caring, and authoritative tone
                6. Structure your response with clear attribution:
                   - Begin with the main teaching from the most relevant source
                   - Support it with related points from other sources
                   - Connect the teachings to practical application
                7. Do not make general statements without source attribution
                
                Context from teachings:
                {context}"""
            }
        ]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": user_message})
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            presence_penalty=0.6,  # Encourage diverse responses
            frequency_penalty=0.3  # Reduce repetition
        )
        
        # Extract response and add source information
        response_content = response.choices[0].message.content
        
        # Add source information to the response if not already present
        if sources_used and "[Source:" not in response_content:
            response_content += f"\n\n[Based on teachings from: {', '.join(sources_used)}]"
        
        return jsonify({
            'response': response_content,
            'conversation_history': messages + [{"role": "assistant", "content": response_content}],
            'sources_used': list(sources_used)
        })
        
    except Exception as e:
        app.logger.error('Error in chat route: %s', str(e))
        return jsonify({'error': 'Could not process your request. Please try again.'}), 500

def get_file_type(filename):
    """Determine the file type from the filename."""
    ext = filename.lower().split('.')[-1]
    if ext == 'wav':
        return 'audio'
    elif ext == 'pdf':
        return 'pdf'
    elif ext == 'docx':
        return 'docx'
    elif ext == 'doc':
        return 'doc'
    elif ext == 'txt':
        return 'txt'
    return 'unsupported'

if __name__ == '__main__':
    print("Starting server on http://127.0.0.1:5001")
    app.run(host='127.0.0.1', port=5001, debug=True) 
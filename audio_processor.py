import os
import speech_recognition as sr
from pydub import AudioSegment
import gc
from typing import Optional, Dict, List
import tempfile
import numpy as np
import wave
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('audio_processor')

def extract_text_from_audio(file_path: str) -> Optional[str]:
    """Extract text from an audio file using speech recognition."""
    try:
        # Convert to absolute path
        abs_path = os.path.abspath(file_path)
        logger.info(f"Starting to process audio file: {abs_path}")
        
        # Get file size in MB
        file_size_mb = os.path.getsize(abs_path) / (1024 * 1024)
        logger.info(f"Audio file size: {file_size_mb:.2f} MB")
        
        # Initialize recognizer
        logger.debug("Initializing speech recognizer")
        recognizer = sr.Recognizer()
        
        # Handle different file types
        if file_path.lower().endswith('.dat'):
            logger.info("Processing .dat file")
            try:
                # Try to process as MP4 container (WhatsApp audio)
                audio = AudioSegment.from_file(abs_path)
                logger.info("Successfully loaded audio as MP4 container")
            except Exception as e:
                logger.error(f"Failed to process as MP4 container: {str(e)}")
                return None
        else:
            # Handle other audio formats (MP3, WAV)
            try:
                logger.info(f"Processing audio file as {os.path.splitext(file_path)[1]} format")
                audio = AudioSegment.from_file(abs_path)
                logger.debug(f"Successfully loaded audio file, duration: {len(audio)}ms")
            except Exception as e:
                logger.error(f"Error loading audio file: {str(e)}")
                return None
        
        # Process in chunks for memory efficiency
        chunk_length_ms = 30000  # 30 seconds per chunk
        chunks = [audio[i:i + chunk_length_ms] for i in range(0, len(audio), chunk_length_ms)]
        logger.info(f"Split audio into {len(chunks)} chunks")
        
        text_segments = []
        no_speech_chunks = 0
        
        for i, chunk in enumerate(chunks):
            try:
                logger.debug(f"Processing chunk {i+1}/{len(chunks)}")
                # Save chunk to temporary WAV file
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                    logger.debug(f"Created temporary file for chunk: {temp_wav.name}")
                    chunk.export(temp_wav.name, format='wav')
                    
                    # Process the chunk
                    with sr.AudioFile(temp_wav.name) as source:
                        logger.debug("Reading chunk audio data")
                        audio_data = recognizer.record(source)
                        logger.debug("Starting Google speech recognition for chunk")
                        text = recognizer.recognize_google(audio_data)
                        if text.strip():  # Only add non-empty text
                            text_segments.append(text)
                            logger.debug(f"Successfully transcribed chunk {i+1}")
                        else:
                            no_speech_chunks += 1
                            logger.warning(f"No speech detected in chunk {i+1}")
                        
                # Clean up temporary file
                try:
                    os.unlink(temp_wav.name)
                except Exception as e:
                    logger.error(f"Error cleaning up chunk temporary file: {str(e)}")
                
                # Force garbage collection for large files
                if file_size_mb > 50 and i % 5 == 0:
                    logger.debug("Running garbage collection")
                    gc.collect()
                    
            except sr.UnknownValueError:
                no_speech_chunks += 1
                logger.warning(f"No speech detected in chunk {i+1}")
                continue
            except sr.RequestError as e:
                logger.error(f"Could not request results from speech recognition service for chunk {i+1}: {e}")
                continue
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {str(e)}")
                continue
        
        if text_segments:
            logger.info(f"Successfully processed {len(text_segments)} chunks with speech")
            if no_speech_chunks > 0:
                logger.warning(f"{no_speech_chunks} chunks contained no speech")
            return ' '.join(text_segments)
        else:
            if no_speech_chunks == len(chunks):
                logger.error("No speech detected in any chunk of the audio file")
            else:
                logger.error("No text segments were successfully processed")
            return None
        
    except Exception as e:
        logger.error(f"Error processing audio file {file_path}: {str(e)}")
        return None

def process_audio_directory(directory_path: str) -> List[Dict]:
    """Process all supported audio files in the specified directory."""
    processed_audio = []
    
    # Get all files in the directory
    try:
        files = os.listdir(directory_path)
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
                if filename.lower().endswith(('.mp3', '.wav', '.dat')):
                    content = extract_text_from_audio(file_path)
                
                if content:
                    # Only keep the first 1000 characters for preview
                    preview_content = content[:1000] + "..." if len(content) > 1000 else content
                    processed_audio.append({
                        'filename': filename,
                        'content': content,
                        'preview': preview_content
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
        
    print(f"Successfully processed {len(processed_audio)} out of {len(files)} files")
    return processed_audio 
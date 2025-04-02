import os
from audio_processor import extract_text_from_audio, process_audio_directory

def test_audio_processing():
    """Test the audio processing functionality."""
    # Create a test directory if it doesn't exist
    test_dir = "test_audio"
    if not os.path.exists(test_dir):
        os.makedirs(test_dir)
        print(f"Created test directory: {test_dir}")
    
    # Test single file processing
    test_file = os.path.join(test_dir, "test.mp3")
    if os.path.exists(test_file):
        print("\nTesting single file processing:")
        result = extract_text_from_audio(test_file)
        if result:
            print("Successfully extracted text from audio file")
            print(f"Preview: {result[:200]}...")
        else:
            print("Failed to extract text from audio file")
    
    # Test directory processing
    print("\nTesting directory processing:")
    results = process_audio_directory(test_dir)
    print(f"Processed {len(results)} files")
    for result in results:
        print(f"\nFile: {result['filename']}")
        print(f"Preview: {result['preview']}")

if __name__ == "__main__":
    test_audio_processing() 
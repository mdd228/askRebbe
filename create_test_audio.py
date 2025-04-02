import pyttsx3
import os

def create_test_speech():
    """Creates a test audio file with a sample teaching."""
    # Create test_audio directory if it doesn't exist
    if not os.path.exists('test_audio'):
        os.makedirs('test_audio')
    
    # Initialize the text-to-speech engine
    engine = pyttsx3.init()
    
    # Configure the voice
    engine.setProperty('rate', 150)    # Slower speed for clarity
    engine.setProperty('volume', 0.9)  # Volume level
    
    # Sample teaching text
    test_text = """
    The purpose of technology is to reveal the divine wisdom in creation.
    When we use modern tools to spread goodness and kindness,
    we elevate the physical world and make it a dwelling place for G-dliness.
    Every new invention is an opportunity to bring more light into the world.
    """
    
    # Save as WAV file
    output_file = 'test_audio/test_teaching.wav'
    engine.save_to_file(test_text, output_file)
    engine.runAndWait()
    
    print(f"Created test audio file at: {output_file}")
    print("Content: Sample teaching about technology and divine purpose")

if __name__ == "__main__":
    create_test_speech() 
import requests
import os

def download_rebbe_audio():
    """
    Downloads a sample audio clip of the Rebbe from Chabad.org's media archive.
    Using a short sicha (talk) as a test sample.
    """
    # Create test_audio directory if it doesn't exist
    if not os.path.exists('test_audio'):
        os.makedirs('test_audio')
    
    # URL for a sample Rebbe audio clip
    # Note: We'll need to replace this with an actual URL from Chabad.org's media archive
    audio_url = "https://www.chabad.org/multimedia/media_cdo/aid/4453082/jewish/The-Rebbe-on-Technology.mp3"
    
    try:
        print("Downloading audio clip of the Rebbe...")
        response = requests.get(audio_url, stream=True)
        
        if response.status_code == 200:
            with open('test_audio/rebbe_tech.mp3', 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print("Successfully downloaded the audio clip")
        else:
            print(f"Failed to download. Status code: {response.status_code}")
            
    except Exception as e:
        print(f"Error downloading the file: {str(e)}")
        print("Please manually download an audio clip from Chabad.org's media archive")
        print("Suggested source: https://www.chabad.org/therebbe/livingtorah/")

if __name__ == "__main__":
    download_rebbe_audio() 
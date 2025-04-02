# Ask Rebbe - AI-Powered Chassidic Wisdom

An intelligent chatbot that provides guidance based on the teachings of the Lubavitcher Rebbe, incorporating audio, text, and document processing capabilities.

## Features

- **Audio Processing**: Transcribes and processes audio teachings of the Rebbe
- **Document Processing**: Handles various document formats (PDF, DOCX, TXT)
- **Semantic Search**: Implements advanced search to find relevant teachings
- **RAG System**: Retrieval-Augmented Generation for context-aware responses
- **Multi-Document Integration**: Combines insights from multiple sources
- **Interactive Chat**: User-friendly interface for asking questions

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ask-rebbe.git
cd ask-rebbe
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
OPENAI_API_KEY=your_api_key_here
```

4. Run the application:
```bash
python app.py
```

## Project Structure

- `app.py`: Main application file
- `audio_processor.py`: Handles audio file processing
- `document_processor.py`: Processes various document formats
- `test_*.py`: Test and demonstration scripts
- `templates/`: HTML templates for the web interface
- `models/`: Data models and database schemas
- `controllers/`: Business logic and route handlers

## Testing

Run the test suite:
```bash
python -m pytest tests/
```

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 
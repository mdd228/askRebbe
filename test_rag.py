import os
import sys
from app import app, process_audio_file, find_relevant_chunks

def test_rag_with_audio():
    """Test if audio content is properly included in the RAG system."""
    # Process the audio file
    audio_content = process_audio_file('test_audio/test_teaching.wav')
    if not audio_content:
        print("Failed to process audio file")
        return False
    
    # Create a processed document
    processed_doc = {
        'filename': 'test_teaching.wav',
        'content': audio_content
    }
    
    # Test queries that should match the audio content
    test_queries = [
        "What is the purpose of technology?",
        "How does technology relate to divine wisdom?",
        "What does the Rebbe say about modern tools?",
        "How can we elevate the physical world?",
        "What is the connection between technology and spirituality?"
    ]
    
    print("\nTesting RAG with audio content:")
    print(f"Audio content length: {len(audio_content)} characters")
    print(f"Audio content preview: {audio_content[:200]}...")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        relevant_chunks = find_relevant_chunks(query, [processed_doc], max_chunks=5)
        
        if relevant_chunks:
            print(f"Found {len(relevant_chunks)} relevant chunks")
            for i, chunk in enumerate(relevant_chunks):
                print(f"Chunk {i+1} similarity: {chunk['similarity']:.4f}")
                print(f"Content: {chunk['content'][:100]}...")
        else:
            print("No relevant chunks found")
    
    return True

if __name__ == "__main__":
    with app.app_context():
        success = test_rag_with_audio()
        if success:
            print("\nRAG test completed successfully")
        else:
            print("\nRAG test failed")
            sys.exit(1) 
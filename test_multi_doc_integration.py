import os
import sys
import json
from app import app, process_audio_file, find_relevant_chunks

def test_multi_doc_integration():
    """Test integration with multiple documents including audio."""
    # Process the audio file
    audio_content = process_audio_file('test_audio/test_teaching.wav')
    if not audio_content:
        print("Failed to process audio file")
        return False
    
    # Create sample documents
    processed_docs = [
        {
            'filename': 'test_teaching.wav',
            'content': audio_content
        },
        {
            'filename': 'torah_study.txt',
            'content': "Torah study is the foundation of Jewish life. Through studying Torah, we connect with the divine wisdom and understand how to live according to G-d's will. The Rebbe emphasizes that Torah study should not be theoretical but should lead to practical action in observing mitzvot."
        },
        {
            'filename': 'mitzvot_observance.txt',
            'content': "The observance of mitzvot is the practical expression of our connection to G-d. When we fulfill mitzvot, we bring holiness into the physical world. The Rebbe teaches that every mitzvah we perform creates a dwelling place for G-d in this world."
        }
    ]
    
    # Add the processed documents to the app context
    app.processed_documents = processed_docs
    
    # Test queries that should match multiple documents
    test_queries = [
        "What is the connection between Torah study and mitzvot?",
        "How does technology relate to divine wisdom?",
        "What does the Rebbe say about bringing holiness into the world?",
        "How can we elevate the physical world?",
        "What is the purpose of Torah study?"
    ]
    
    print("\nTesting multi-document integration:")
    for doc in processed_docs:
        print(f"\nDocument: {doc['filename']}")
        print(f"Content length: {len(doc['content'])} characters")
        print(f"Content preview: {doc['content'][:200]}...")
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Simulate the chat route
        try:
            # Find relevant chunks
            relevant_chunks = find_relevant_chunks(query, app.processed_documents, max_chunks=5)
            
            # Create context from relevant chunks
            context_parts = []
            sources_used = set()
            
            for chunk in relevant_chunks:
                source = chunk['source']
                sources_used.add(source)
                context_parts.append(f"[Source: {source}]\n{chunk['content']}\n")
            
            context = "\n\n".join(context_parts)
            
            # If no relevant chunks found, use a small sample from each document
            if not context:
                print("No relevant chunks found, using document samples")
                for doc in app.processed_documents[:5]:
                    sample = doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content']
                    context_parts.append(f"[Source: {doc['filename']}]\n{sample}\n")
                    sources_used.add(doc['filename'])
                context = "\n\n".join(context_parts)
            
            print(f"Context length: {len(context)} characters")
            print(f"Sources used: {', '.join(sources_used)}")
            print(f"Context preview: {context[:200]}...")
            
        except Exception as e:
            print(f"Error in multi-document integration: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    with app.app_context():
        success = test_multi_doc_integration()
        if success:
            print("\nMulti-document integration test completed successfully")
        else:
            print("\nMulti-document integration test failed")
            sys.exit(1) 
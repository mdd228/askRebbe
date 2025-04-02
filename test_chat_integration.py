import os
import sys
import json
from app import app, process_audio_file, find_relevant_chunks

def test_chat_integration():
    """Test the full integration with the chat route."""
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
    
    # Add the processed document to the app context
    app.processed_documents = [processed_doc]
    
    # Test queries that should match the audio content
    test_queries = [
        "What is the purpose of technology?",
        "How does technology relate to divine wisdom?",
        "What does the Rebbe say about modern tools?",
        "How can we elevate the physical world?",
        "What is the connection between technology and spirituality?"
    ]
    
    print("\nTesting chat integration with audio content:")
    print(f"Audio content length: {len(audio_content)} characters")
    print(f"Audio content preview: {audio_content[:200]}...")
    
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
            print(f"Error in chat integration: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    with app.app_context():
        success = test_chat_integration()
        if success:
            print("\nChat integration test completed successfully")
        else:
            print("\nChat integration test failed")
            sys.exit(1) 
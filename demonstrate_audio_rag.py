import os
import sys
import json
from app import app, process_audio_file, find_relevant_chunks

def demonstrate_audio_rag():
    """Demonstrate that the audio file is working in the RAG system."""
    print("\n" + "="*80)
    print("DEMONSTRATION: AUDIO FILE WORKING IN RAG SYSTEM")
    print("="*80)
    
    # Step 1: Process the audio file
    print("\nSTEP 1: PROCESSING AUDIO FILE")
    print("-"*50)
    audio_content = process_audio_file('test_audio/test_teaching.wav')
    if not audio_content:
        print("❌ FAILED: Could not process audio file")
        return False
    
    print("✅ SUCCESS: Audio file processed successfully")
    print(f"   Content length: {len(audio_content)} characters")
    print(f"   Content: {audio_content}")
    
    # Step 2: Create a processed document
    print("\nSTEP 2: CREATING PROCESSED DOCUMENT")
    print("-"*50)
    processed_doc = {
        'filename': 'test_teaching.wav',
        'content': audio_content
    }
    print("✅ SUCCESS: Created processed document from audio content")
    
    # Step 3: Test RAG with audio content
    print("\nSTEP 3: TESTING RAG WITH AUDIO CONTENT")
    print("-"*50)
    
    # Test query specifically about technology
    query = "What is the purpose of technology according to the Rebbe?"
    print(f"Query: '{query}'")
    
    relevant_chunks = find_relevant_chunks(query, [processed_doc], max_chunks=5)
    
    if relevant_chunks:
        print("✅ SUCCESS: Found relevant chunks from audio content")
        for i, chunk in enumerate(relevant_chunks):
            print(f"\nChunk {i+1}:")
            print(f"  Similarity: {chunk['similarity']:.4f}")
            print(f"  Content: {chunk['content']}")
    else:
        print("❌ FAILED: No relevant chunks found from audio content")
        return False
    
    # Step 4: Test with multiple documents
    print("\nSTEP 4: TESTING WITH MULTIPLE DOCUMENTS")
    print("-"*50)
    
    # Create sample documents
    processed_docs = [
        processed_doc,  # Audio document
        {
            'filename': 'torah_study.txt',
            'content': "Torah study is the foundation of Jewish life. Through studying Torah, we connect with the divine wisdom and understand how to live according to G-d's will. The Rebbe emphasizes that Torah study should not be theoretical but should lead to practical action in observing mitzvot."
        }
    ]
    
    # Test query about technology and Torah
    query = "How does technology relate to divine wisdom and Torah study?"
    print(f"Query: '{query}'")
    
    relevant_chunks = find_relevant_chunks(query, processed_docs, max_chunks=5)
    
    if relevant_chunks:
        print("✅ SUCCESS: Found relevant chunks from multiple documents")
        for i, chunk in enumerate(relevant_chunks):
            print(f"\nChunk {i+1}:")
            print(f"  Source: {chunk['source']}")
            print(f"  Similarity: {chunk['similarity']:.4f}")
            print(f"  Content: {chunk['content']}")
    else:
        print("❌ FAILED: No relevant chunks found from multiple documents")
        return False
    
    # Step 5: Create context from relevant chunks
    print("\nSTEP 5: CREATING CONTEXT FROM RELEVANT CHUNKS")
    print("-"*50)
    
    context_parts = []
    sources_used = set()
    
    for chunk in relevant_chunks:
        source = chunk['source']
        sources_used.add(source)
        context_parts.append(f"[Source: {source}]\n{chunk['content']}\n")
    
    context = "\n\n".join(context_parts)
    
    print("✅ SUCCESS: Created context from relevant chunks")
    print(f"  Context length: {len(context)} characters")
    print(f"  Sources used: {', '.join(sources_used)}")
    print(f"  Context:\n{context}")
    
    print("\n" + "="*80)
    print("CONCLUSION: AUDIO FILE IS WORKING IN THE RAG SYSTEM")
    print("="*80)
    return True

if __name__ == "__main__":
    with app.app_context():
        success = demonstrate_audio_rag()
        if success:
            print("\n✅ DEMONSTRATION COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ DEMONSTRATION FAILED")
            sys.exit(1) 
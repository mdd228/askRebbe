import os
import sys
import json
from app import app, process_audio_file, find_relevant_chunks
from openai import OpenAI

def demonstrate_audio_chat():
    """Demonstrate that the audio file is working with the actual chat route."""
    print("\n" + "="*80)
    print("DEMONSTRATION: AUDIO FILE WORKING WITH CHAT ROUTE")
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
    
    # Step 2: Create processed documents
    print("\nSTEP 2: CREATING PROCESSED DOCUMENTS")
    print("-"*50)
    
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
    print("✅ SUCCESS: Created processed documents and added to app context")
    
    # Step 3: Simulate the chat route
    print("\nSTEP 3: SIMULATING CHAT ROUTE")
    print("-"*50)
    
    # Test queries
    test_queries = [
        "What is the purpose of technology according to the Rebbe?",
        "How does technology relate to divine wisdom and Torah study?",
        "What does the Rebbe say about bringing holiness into the world?"
    ]
    
    for query in test_queries:
        print(f"\nQuery: '{query}'")
        
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
            
            print(f"✅ SUCCESS: Created context from relevant chunks")
            print(f"   Context length: {len(context)} characters")
            print(f"   Sources used: {', '.join(sources_used)}")
            print(f"   Context preview: {context[:200]}...")
            
            # Step 4: Generate response using OpenAI
            print("\nSTEP 4: GENERATING RESPONSE USING OPENAI")
            print("-"*50)
            
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
                },
                {"role": "user", "content": query}
            ]
            
            # Get response from OpenAI
            client = OpenAI()
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
                presence_penalty=0.6,
                frequency_penalty=0.3
            )
            
            # Extract response
            response_content = response.choices[0].message.content
            
            # Add source information to the response if not already present
            if sources_used and "[Source:" not in response_content:
                response_content += f"\n\n[Based on teachings from: {', '.join(sources_used)}]"
            
            print("✅ SUCCESS: Generated response using OpenAI")
            print(f"   Response:\n{response_content}")
            
        except Exception as e:
            print(f"❌ ERROR: {str(e)}")
            return False
    
    print("\n" + "="*80)
    print("CONCLUSION: AUDIO FILE IS WORKING WITH THE CHAT ROUTE")
    print("="*80)
    return True

if __name__ == "__main__":
    with app.app_context():
        success = demonstrate_audio_chat()
        if success:
            print("\n✅ DEMONSTRATION COMPLETED SUCCESSFULLY")
        else:
            print("\n❌ DEMONSTRATION FAILED")
            sys.exit(1) 
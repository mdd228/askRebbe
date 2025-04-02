import os
from typing import List, Optional, Dict
from models.document import Document

class DocumentController:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(base_dir)
        self.documents: Dict[str, Document] = {}
        self.supported_extensions = ['.pdf', '.doc', '.docx', '.txt']
        
    def scan_directory(self) -> List[str]:
        """Scan the base directory for supported documents."""
        found_files = []
        # Clear existing documents to prevent stale references
        self.documents.clear()
        
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in self.supported_extensions):
                    full_path = os.path.abspath(os.path.join(root, file))
                    if os.path.exists(full_path):  # Double check file exists
                        found_files.append(full_path)
                        # Create Document instance if not already exists
                        if full_path not in self.documents:
                            self.documents[full_path] = Document(full_path)
        return found_files
    
    def process_document(self, file_path: str) -> Optional[str]:
        """Process a single document and return its content."""
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            print(f"File does not exist: {abs_path}")
            return None
            
        # If this is a temporary DOCX file created from a DOC file, skip it
        if abs_path.endswith('.docx'):
            doc_path = abs_path.replace('.docx', '.doc')
            if os.path.exists(doc_path):
                print(f"Skipping temporary DOCX file: {abs_path}")
                return None
                
        if abs_path not in self.documents:
            self.documents[abs_path] = Document(abs_path)
        
        doc = self.documents[abs_path]
        content = doc.extract_content()
        if content is None:
            print(f"Failed to extract content from: {abs_path}")
        return content
    
    def process_all_documents(self) -> Dict[str, Optional[str]]:
        """Process all documents in the base directory."""
        # First scan to ensure we have all current files
        found_files = self.scan_directory()
        print(f"Found {len(found_files)} files to process")
        
        results = {}
        # Process each document that exists
        for file_path in found_files:
            if os.path.exists(file_path):  # Verify file still exists
                print(f"Processing file: {file_path}")
                content = self.process_document(file_path)
                if content is not None:  # Only include successfully processed files
                    results[file_path] = content
            else:
                print(f"File no longer exists: {file_path}")
        return results
    
    def get_document_content(self, file_path: str) -> Optional[str]:
        """Get content of a specific document."""
        abs_path = os.path.abspath(file_path)
        if abs_path in self.documents and os.path.exists(abs_path):
            return self.documents[abs_path].content
        return None
    
    def get_all_documents(self) -> List[Dict]:
        """Get all documents as list of dictionaries."""
        # First scan to ensure we have current files
        self.scan_directory()
        return [doc.to_dict() for doc in self.documents.values()] 
import unittest
import sys
import os

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the test
from tests.test_document import TestDocumentProcessing

if __name__ == '__main__':
    print("Running document processing tests...")
    unittest.main(verbosity=2) 
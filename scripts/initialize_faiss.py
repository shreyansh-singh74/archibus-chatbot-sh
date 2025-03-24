import sys
import os
import numpy as np
import pickle

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.faiss_store import FAISSDocumentStore
from sentence_transformers import SentenceTransformer

def initialize_faiss():
    print("Initializing FAISS index with sample data...")
    
    # Create sample data
    sample_documents = [
        "Archibus space management features and capabilities",
        "How to book a meeting room in Archibus",
        "Archibus maintenance management workflow",
        "Building operations dashboard in Archibus",
        "Archibus mobile app features"
    ]
    
    # Sample image URLs (replace with actual URLs from your application)
    sample_image_urls = [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
        "https://example.com/image3.jpg",
        "https://example.com/image4.jpg",
        "https://example.com/image5.jpg"
    ]
    
    # Create sample IDs
    sample_ids = [f"doc_{i}" for i in range(len(sample_documents))]
    
    # Create sample metadata
    sample_metadata = [{"image_url": url} for url in sample_image_urls]
    
    # Create embeddings
    print("Generating embeddings for sample documents...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(sample_documents)
    
    # Create FAISS document store
    faiss_store = FAISSDocumentStore()
    
    # Add data to FAISS
    faiss_store.add(
        documents=sample_image_urls,  # We store image URLs as documents
        embeddings=embeddings,
        ids=sample_ids,
        metadatas=sample_metadata
    )
    
    # Define paths for saving
    index_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_index.idx")
    metadata_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_metadata.pkl")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    
    # Save FAISS index and metadata
    faiss_store.save(index_path, metadata_path)
    
    print(f"Successfully created FAISS index with {len(sample_documents)} sample documents")
    print(f"FAISS index saved to: {index_path}")
    print(f"Metadata saved to: {metadata_path}")

if __name__ == "__main__":
    initialize_faiss()
import re
import os
import sys
from sentence_transformers import SentenceTransformer

# Add parent directory to path if needed
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.faiss_store import FAISSDocumentStore

# Load model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

# Setup paths for FAISS index and metadata
index_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_index.idx")
metadata_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_metadata.pkl")

# Initialize FAISS document store
faiss_store = FAISSDocumentStore(index_path=index_path, metadata_path=metadata_path)

def find_relevant_images(query, top_k=5):
    """Find relevant images using FAISS"""
    try:
        # Check if index exists
        if faiss_store.index is None:
            print("Warning: FAISS index not found or empty")
            return []
        
        # Embed the query
        query_embedding = model.encode([query])
        
        # Add debugging info
        print(f"Query: {query}")
        print(f"Embedding shape: {query_embedding.shape}")
        print(f"FAISS index total: {faiss_store.index.ntotal}")
        
        # Search the FAISS index
        results = faiss_store.query(query_embeddings=query_embedding, n_results=top_k)
        
        # More debugging info
        print(f"Search results: {results.keys() if results else None}")
        
        # Extract the documents (image URLs)
        if results and "documents" in results and len(results["documents"]) > 0:
            image_urls = results["documents"][0]
            print(f"Found {len(image_urls)} images: {image_urls}")
            return image_urls
        else:
            print("No images found in results")
    except Exception as e:
        import traceback
        print(f"Error finding images: {str(e)}")
        traceback.print_exc()
    
    return []
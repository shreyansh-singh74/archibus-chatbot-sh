import chromadb
import os
import sys
import pickle
import faiss
import numpy as np

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.faiss_store import FAISSDocumentStore

def migrate_chromadb_to_faiss():
    """Migrate data from ChromaDB to FAISS"""
    print("Starting migration from ChromaDB to FAISS...")
    
    # Initialize ChromaDB client
    # Change this to match your ChromaDB setup
    try:
        chroma_client = chromadb.PersistentClient(path="chromadb_data")
        # Adjust collection name if needed
        collection_name = "document_collection"  
        print(f"Looking for ChromaDB collection: {collection_name}")
        collection = chroma_client.get_collection(name=collection_name)
        print("Found existing ChromaDB collection")
    except Exception as e:
        print(f"Error accessing ChromaDB collection: {e}")
        return
    
    # Get all data from ChromaDB
    try:
        all_data = collection.get()
        print(f"Retrieved {len(all_data['ids'])} documents from ChromaDB")
    except Exception as e:
        print(f"Error retrieving data from ChromaDB: {e}")
        return
    
    # Check if we have data to migrate
    if not all_data['ids']:
        print("No data to migrate")
        return
    
    # Create FAISS document store
    faiss_store = FAISSDocumentStore()
    
    # Add data to FAISS
    faiss_store.add(
        documents=all_data['documents'],
        embeddings=all_data['embeddings'],
        ids=all_data['ids'],
        metadatas=all_data.get('metadatas', [{}] * len(all_data['ids']))
    )
    
    # Define paths for saving
    index_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_index.idx")
    metadata_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_metadata.pkl")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    
    # Save FAISS index and metadata
    faiss_store.save(index_path, metadata_path)
    
    print(f"Successfully migrated {len(all_data['ids'])} documents to FAISS")
    print(f"FAISS index saved to: {index_path}")
    print(f"Metadata saved to: {metadata_path}")

if __name__ == "__main__":
    migrate_chromadb_to_faiss()
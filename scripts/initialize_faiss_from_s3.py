import os
import sys
import json
import numpy as np
from sentence_transformers import SentenceTransformer

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.faiss_store import FAISSDocumentStore

def initialize_faiss_from_s3_mapping():
    print("Initializing FAISS index from S3 image mapping...")
    
    # Path to image mapping JSON file
    json_path = os.path.join(os.path.dirname(__file__), "..", "Extractor", "s3_upload", "image_mapping.json")
    
    # Load the image mappings
    with open(json_path, 'r') as f:
        image_mappings = json.load(f)
    
    print(f"Loaded {len(image_mappings)} image mappings")
    
    # Extract text descriptions and image URLs
    texts = []
    image_urls = []
    ids = []
    metadatas = []
    
    for i, mapping in enumerate(image_mappings):
        if not isinstance(mapping, dict) or 's3_url' not in mapping:
            continue
            
        # Create a description from the PDF source and image name
        description = ""
        if 'pdf_source' in mapping:
            # Remove .pdf extension and clean up the name
            pdf_name = mapping['pdf_source'].replace('.pdf.pdf', '').replace('.pdf', '')
            description += pdf_name + " "
            
        if 'image_name' in mapping:
            # Clean up image name
            img_name = mapping['image_name'].replace('.png', '').replace('_page', ' page ').replace('_img', ' image ')
            description += img_name
            
        texts.append(description)
        image_urls.append(mapping['s3_url'])
        ids.append(f"img_{i}")
        
        # Create metadata for additional information
        metadata = {
            'image_name': mapping.get('image_name', ''),
            'pdf_source': mapping.get('pdf_source', ''),
            'page_number': mapping.get('page_number', 0),
            'image_url': mapping['s3_url']
        }
        metadatas.append(metadata)
    
    print(f"Generating embeddings for {len(texts)} documents...")
    
    # Generate embeddings using sentence transformer
    model = SentenceTransformer('all-MiniLM-L6-v2')
    embeddings = model.encode(texts)
    
    print("Embeddings generated successfully")
    
    # Initialize FAISS store
    faiss_store = FAISSDocumentStore()
    
    # Add data to FAISS
    print("Adding data to FAISS index...")
    faiss_store.add(
        documents=image_urls,  # Store image URLs directly as documents
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas
    )
    
    # Define paths for saving
    index_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_index.idx")
    metadata_path = os.path.join(os.path.dirname(__file__), "..", "data", "faiss_metadata.pkl")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(index_path), exist_ok=True)
    
    # Save FAISS index and metadata
    print("Saving FAISS index...")
    faiss_store.save(index_path, metadata_path)
    
    print(f"Successfully created FAISS index with {len(texts)} images")
    print(f"FAISS index saved to: {index_path}")
    print(f"Metadata saved to: {metadata_path}")

if __name__ == "__main__":
    initialize_faiss_from_s3_mapping()
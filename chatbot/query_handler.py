import chromadb
from sentence_transformers import SentenceTransformer

# Load ChromaDB
db_path = "D:\\test\\Extractor\\s3_upload\\chromadb"
chroma_client = chromadb.PersistentClient(path=db_path)
collection = chroma_client.get_or_create_collection(name="image_mapping_metadata")

# Load embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def find_relevant_images(prompt, top_k=5):
    """Finds the most relevant images based on user query."""
    query_embedding = embed_model.encode(prompt).tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,  # Retrieve multiple images
        include=["metadatas"]
    )

    images = []
    if results and "metadatas" in results:
        for metadata_list in results["metadatas"]:
            for metadata in metadata_list:
                if "s3_url" in metadata:
                    images.append(metadata["s3_url"])
    
    return images if images else None  # Return list of images

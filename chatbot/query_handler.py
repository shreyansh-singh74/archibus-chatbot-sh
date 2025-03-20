import chromadb
from sentence_transformers import SentenceTransformer

# Load ChromaDB
db_path = "D:\\test\\Extractor\\s3_upload\\chromadb"
chroma_client = chromadb.PersistentClient(path=db_path)
collection = chroma_client.get_or_create_collection(name="image_mapping_metadata")

# Load embedding model
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

def find_relevant_image(prompt):
    """Finds the most relevant image based on user query."""
    query_embedding = embed_model.encode(prompt).tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=5,
        include=["metadatas"]
    )

    if results and "metadatas" in results and results["metadatas"][0]:
        metadata = results["metadatas"][0][0]
        return metadata.get("s3_url", None)

    return None

import numpy as np
import faiss
import pickle
import os
from typing import List, Dict, Any, Optional

class FAISSDocumentStore:
    def __init__(self, index_path=None, metadata_path=None):
        self.index = None
        self.documents = []
        self.ids = []
        self.metadata = []
        
        # Load existing index if provided
        if index_path and os.path.exists(index_path):
            self.index = faiss.read_index(index_path)
            
        # Load existing metadata if provided    
        if metadata_path and os.path.exists(metadata_path):
            with open(metadata_path, 'rb') as f:
                data = pickle.load(f)
                self.documents = data.get('documents', [])
                self.ids = data.get('ids', [])
                self.metadata = data.get('metadata', [])
    
    def add(self, documents: List[str], embeddings: List[List[float]], ids: List[str], metadatas: Optional[List[Dict[str, Any]]] = None):
        """Add documents with their embeddings and metadata to the FAISS index"""
        
        # Convert embeddings to numpy array
        embeddings_np = np.array(embeddings).astype('float32')
        
        # Create index if it doesn't exist
        if self.index is None:
            dimension = embeddings_np.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
        
        # Add vectors to the index
        self.index.add(embeddings_np)
        
        # Store documents, ids, and metadata
        self.documents.extend(documents)
        self.ids.extend(ids)
        
        if metadatas:
            self.metadata.extend(metadatas)
        else:
            self.metadata.extend([{}] * len(documents))  # Empty metadata for each document
    
    def query(self, query_embeddings: List[List[float]], n_results: int = 3):
        """Search for similar documents"""
        if self.index is None or self.index.ntotal == 0:
            return {"ids": [], "documents": [], "distances": []}
            
        # Convert query embedding to numpy array
        query_np = np.array(query_embeddings).astype('float32')
        
        # Search the index
        distances, indices = self.index.search(query_np, min(n_results, self.index.ntotal))
        
        # Gather results
        result_ids = []
        result_documents = []
        
        for query_indices in indices:
            query_ids = []
            query_documents = []
            
            for idx in query_indices:
                if 0 <= idx < len(self.ids):
                    query_ids.append(self.ids[idx])
                    query_documents.append(self.documents[idx])
            
            result_ids.append(query_ids)
            result_documents.append(query_documents)
        
        return {
            "ids": result_ids,
            "documents": result_documents,
            "distances": distances.tolist()
        }
    
    def delete(self, ids: List[str]):
        """Delete documents by their IDs"""
        # FAISS doesn't support direct deletion by ID
        # We need to rebuild the index without the deleted documents
        if not ids or self.index is None:
            return
            
        # Find indices to keep
        indices_to_keep = []
        for i, doc_id in enumerate(self.ids):
            if doc_id not in ids:
                indices_to_keep.append(i)
        
        if not indices_to_keep:
            # All documents deleted
            self.index = None
            self.documents = []
            self.ids = []
            self.metadata = []
            return
            
        # Extract data to keep
        new_documents = [self.documents[i] for i in indices_to_keep]
        new_ids = [self.ids[i] for i in indices_to_keep]
        new_metadata = [self.metadata[i] for i in indices_to_keep]
        
        # Get embeddings from the index
        total = self.index.ntotal
        dimension = self.index.d
        old_embeddings = np.zeros((total, dimension), dtype=np.float32)
        for i in range(total):
            old_embeddings[i] = self.index.reconstruct(i)
        
        # Select embeddings to keep
        new_embeddings = np.array([old_embeddings[i] for i in indices_to_keep]).astype('float32')
        
        # Create new index
        new_index = faiss.IndexFlatL2(dimension)
        new_index.add(new_embeddings)
        
        # Update instance variables
        self.index = new_index
        self.documents = new_documents
        self.ids = new_ids
        self.metadata = new_metadata
    
    def get_or_create_collection(self, name):
        """Method to mimic ChromaDB's get_or_create_collection"""
        # FAISS doesn't have collections like ChromaDB
        # Just return self for API compatibility
        return self
        
    def save(self, index_path, metadata_path):
        """Save the index and metadata to disk"""
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(index_path), exist_ok=True)
        os.makedirs(os.path.dirname(metadata_path), exist_ok=True)
        
        # Save index
        if self.index is not None:
            faiss.write_index(self.index, index_path)
        
        # Save metadata
        with open(metadata_path, 'wb') as f:
            data = {
                'documents': self.documents,
                'ids': self.ids,
                'metadata': self.metadata
            }
            pickle.dump(data, f)
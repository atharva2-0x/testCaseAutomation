"""Vector store implementation using FAISS."""
import uuid
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
import faiss
from core.config import settings
from core.logger import log


class VectorStore:
    """FAISS-based vector storage with metadata."""
    
    def __init__(self):
        self.index = None
        self.documents = {}  # doc_id -> {text, metadata}
        self.dimension = settings.embedding_dim
        self.index_path = settings.vector_db_path / "faiss.index"
        self.metadata_path = settings.vector_db_path / "metadata.pkl"
        
        # Create directory
        settings.vector_db_path.mkdir(parents=True, exist_ok=True)
        
        # Load existing index or create new
        self._load_or_create_index()
    
    def _load_or_create_index(self):
        """Load existing index or create new one."""
        if self.index_path.exists() and self.metadata_path.exists():
            try:
                self.index = faiss.read_index(str(self.index_path))
                with open(self.metadata_path, 'rb') as f:
                    self.documents = pickle.load(f)
                log.info(f"Loaded existing vector index with {self.index.ntotal} vectors")
            except Exception as e:
                log.warning(f"Failed to load index: {e}, creating new one")
                self._create_new_index()
        else:
            self._create_new_index()
    
    def _create_new_index(self):
        """Create a new FAISS index."""
        # Using IndexFlatL2 for exact search (can be changed to IndexIVFFlat for speed)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = {}
        log.info(f"Created new FAISS index with dimension {self.dimension}")
    
    def add_document(self, text: str, metadata: Dict, embedding: np.ndarray) -> str:
        """Add a document with its embedding to the store."""
        doc_id = str(uuid.uuid4())
        
        # Ensure embedding is 2D
        if embedding.ndim == 1:
            embedding = embedding.reshape(1, -1)
        
        # Add to FAISS index
        self.index.add(embedding.astype('float32'))
        
        # Store metadata
        self.documents[doc_id] = {
            'text': text,
            'metadata': metadata,
            'index_position': self.index.ntotal - 1
        }
        
        return doc_id
    
    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> List[Dict]:
        """Search for similar documents."""
        if self.index.ntotal == 0:
            return []
        
        # Ensure query is 2D
        if query_embedding.ndim == 1:
            query_embedding = query_embedding.reshape(1, -1)
        
        # Search
        distances, indices = self.index.search(query_embedding.astype('float32'), min(top_k, self.index.ntotal))
        
        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:  # No more results
                break
            
            # Find document by index position
            doc = self._get_document_by_index(idx)
            if doc:
                results.append({
                    'text': doc['text'],
                    'metadata': doc['metadata'],
                    'score': float(1 / (1 + dist)),  # Convert distance to similarity score
                    'distance': float(dist)
                })
        
        return results
    
    def _get_document_by_index(self, index_position: int) -> Optional[Dict]:
        """Find document by its FAISS index position."""
        for doc_id, doc_data in self.documents.items():
            if doc_data['index_position'] == index_position:
                return doc_data
        return None
    
    def save(self):
        """Persist index and metadata to disk."""
        try:
            faiss.write_index(self.index, str(self.index_path))
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.documents, f)
            log.info(f"Saved vector index with {self.index.ntotal} vectors")
        except Exception as e:
            log.error(f"Failed to save vector index: {e}")
            raise
    
    def clear(self):
        """Clear the index and metadata."""
        self._create_new_index()
        if self.index_path.exists():
            self.index_path.unlink()
        if self.metadata_path.exists():
            self.metadata_path.unlink()
        log.info("Cleared vector store")
    
    def __del__(self):
        """Save on cleanup."""
        if self.index and self.index.ntotal > 0:
            try:
                self.save()
            except:
                pass
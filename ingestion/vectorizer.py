"""Vectorization and vector database management with one-time indexing."""
import json
import os
from typing import List, Dict, Any, Union, Optional
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
from core.config import settings
from core.logger import log
from core.utils import compute_file_hash, load_json, save_json, chunk_text
from storage.vector_store import VectorStore


class Vectorizer:
    """Handle document vectorization with deduplication tracking."""
    
    def __init__(self, fiservai_client: Optional[Any] = None):
        """
        Initialize vectorizer with embedding provider.
        
        Args:
            fiservai_client: Optional FiservAI client instance for embeddings
        """
        self.embedding_provider = settings.embedding_provider
        self.fiservai_client = fiservai_client
        self.embedding_model = None
        
        # Initialize embedding model based on provider
        if self.embedding_provider == "sentence_transformers":
            self._init_sentence_transformers()
        elif self.embedding_provider == "fiservai":
            self._init_fiservai()
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
        
        self.vector_store = VectorStore()
        self.tracker_file = settings.vectorized_files_tracker
        self.vectorized_files = self._load_tracker()
    
    def _init_sentence_transformers(self):
        """Initialize sentence-transformers embedding model."""
        # Force fresh download by clearing cache if model fails to load
        max_retries = 2
        for attempt in range(max_retries):
            try:
                self.embedding_model = SentenceTransformer(settings.embedding_model)
                log.info(f"Initialized sentence-transformers with model: {settings.embedding_model}")
                break  # Success, exit retry loop
            except (ValueError, OSError, FileNotFoundError) as e:
                error_str = str(e)
                if (("Unrecognized model" in error_str or "config.json" in error_str or "No such file" in error_str) 
                    and attempt < max_retries - 1):
                    import shutil
                    import json
                    log.warning(f"Model load failed (attempt {attempt + 1}), fixing cache structure...")
                    
                    cache_dir = f"{os.path.expanduser('~')}/.cache/torch/sentence_transformers"
                    model_cache = os.path.join(cache_dir, f"sentence-transformers_{settings.embedding_model}")
                    
                    # Try to fix cache structure first
                    if os.path.exists(model_cache):
                        snapshot_path = None
                        # Find the snapshot directory
                        for root, dirs, files in os.walk(model_cache):
                            if 'snapshots' in root and os.path.basename(root) not in ['snapshots']:
                                snapshot_path = root
                                break
                        
                        if snapshot_path:
                            # Copy/link config.json to cache root
                            config_src = os.path.join(snapshot_path, 'config.json')
                            config_dst = os.path.join(model_cache, 'config.json')
                            if os.path.exists(config_src) and not os.path.exists(config_dst):
                                shutil.copy2(config_src, config_dst)
                            
                            # Link model files to cache root
                            for item in os.listdir(snapshot_path):
                                src = os.path.join(snapshot_path, item)
                                dst = os.path.join(model_cache, item)
                                if os.path.isfile(src) and not os.path.exists(dst):
                                    try:
                                        os.symlink(os.path.relpath(src, model_cache), dst)
                                    except:
                                        try:
                                            shutil.copy2(src, dst)
                                        except:
                                            pass
                            
                            # Copy Pooling config if needed
                            pooling_src = os.path.join(snapshot_path, '1_Pooling', 'config.json')
                            pooling_dst = os.path.join(model_cache, '1_Pooling', 'config.json')
                            if os.path.exists(pooling_src):
                                os.makedirs(os.path.dirname(pooling_dst), exist_ok=True)
                                shutil.copy2(pooling_src, pooling_dst)
                            elif not os.path.exists(pooling_dst):
                                # Create default pooling config
                                os.makedirs(os.path.dirname(pooling_dst), exist_ok=True)
                                with open(pooling_dst, 'w') as f:
                                    json.dump({
                                        "word_embedding_dimension": settings.embedding_dim,
                                        "pooling_mode_cls_token": False,
                                        "pooling_mode_mean_tokens": True,
                                        "pooling_mode_max_tokens": False,
                                        "pooling_mode_mean_sqrt_len_tokens": False
                                    }, f, indent=2)
                            
                            log.info("Cache structure fixed, retrying model load...")
                        else:
                            # If we can't fix it, clear and retry
                            shutil.rmtree(model_cache, ignore_errors=True)
                            log.info("Caches cleared, will re-download...")
                    else:
                        # Cache doesn't exist, will download fresh
                        log.info("No cache found, will download model...")
                else:
                    raise  # Re-raise if not a cache issue or last attempt
    
    def _init_fiservai(self):
        """Initialize FiservAI embedding client."""
        if not self.fiservai_client:
            # Try to get FiservAI client from settings if LLM provider is FiservAI
            if settings.llm_provider == "fiservai":
                try:
                    from llm.client import LLMClient
                    llm_client = LLMClient()
                    self.fiservai_client = llm_client.client
                except Exception as e:
                    log.warning(f"Could not reuse LLM client for embeddings: {e}")
                    # Fall through to create new client
                    self.fiservai_client = None
            
            # Create FiservAI client directly if not using it for LLM or if reuse failed
            if not self.fiservai_client:
                try:
                    from fiservai import FiservAI
                    api_key, api_secret, base_url = settings.get_fiservai_credentials()
                    self.fiservai_client = FiservAI.FiservAI(api_key, api_secret, base_url)
                except Exception as e:
                    raise ValueError(f"Failed to initialize FiservAI client: {e}. Make sure FISERVAI_API_KEY and FISERVAI_API_SECRET are set.")
        
        if not self.fiservai_client:
            raise ValueError("FiservAI client not initialized")
        
        log.info("Initialized FiservAI embedding client")
    
    def _load_tracker(self) -> Dict:
        """Load tracking file to see what's already vectorized."""
        return load_json(self.tracker_file)
    
    def _save_tracker(self):
        """Save tracking information."""
        save_json(self.tracker_file, self.vectorized_files)
    
    def is_file_vectorized(self, file_path: Path) -> bool:
        """Check if file has already been vectorized."""
        file_key = str(file_path.absolute())
        
        if file_key not in self.vectorized_files:
            return False
        
        # Check if file hash matches (detect modifications)
        try:
            current_hash = compute_file_hash(file_path)
            stored_hash = self.vectorized_files[file_key].get('hash')
            return current_hash == stored_hash
        except:
            return False
    
    def mark_file_vectorized(self, file_path: Path, doc_ids: List[str]):
        """Mark file as vectorized with metadata."""
        file_key = str(file_path.absolute())
        file_hash = compute_file_hash(file_path)
        
        self.vectorized_files[file_key] = {
            'hash': file_hash,
            'doc_ids': doc_ids,
            'timestamp': str(Path(file_path).stat().st_mtime),
            'name': file_path.name
        }
        self._save_tracker()
        log.info(f"Marked {file_path.name} as vectorized with {len(doc_ids)} chunks")
    
    def vectorize_file(self, file_path: Path, file_type: str, parsed_data: Any = None) -> List[str]:
        """
        Vectorize a file if not already done.
        Returns list of document IDs.
        """
        # Check if already vectorized
        if self.is_file_vectorized(file_path):
            log.info(f"Skipping {file_path.name} - already vectorized")
            return self.vectorized_files[str(file_path.absolute())]['doc_ids']
        
        log.info(f"Vectorizing {file_path.name} ({file_type})")
        
        # Prepare documents based on file type
        if file_type == "html":
            documents = self._prepare_html_documents(parsed_data)
        elif file_type == "feature":
            documents = self._prepare_feature_documents(parsed_data)
        elif file_type == "stepdef":
            documents = self._prepare_stepdef_documents(parsed_data)
        elif file_type == "pageobject":
            documents = self._prepare_pageobject_documents(parsed_data)
        else:
            log.error(f"Unknown file type: {file_type}")
            return []
        
        # Vectorize and store
        doc_ids = []
        for doc in documents:
            doc_id = self.vector_store.add_document(
                text=doc['text'],
                metadata={
                    'source': str(file_path),
                    'type': file_type,
                    **doc.get('metadata', {})
                },
                embedding=self.embed_text(doc['text'])
            )
            doc_ids.append(doc_id)
        
        # Mark as vectorized
        self.mark_file_vectorized(file_path, doc_ids)
        
        return doc_ids
    
    def embed_text(self, text: str) -> np.ndarray:
        """Generate embedding for text."""
        if self.embedding_provider == "sentence_transformers":
            return self.embedding_model.encode(text, convert_to_numpy=True)
        elif self.embedding_provider == "fiservai":
            if not self.fiservai_client:
                raise ValueError("FiservAI client not initialized")
            embeddings, info = self.fiservai_client.get_embeddings(text, show_progress=True)
            # Handle both single string and list returns
            if isinstance(embeddings, list) and len(embeddings) > 0:
                return np.array(embeddings[0], dtype=np.float32)
            elif isinstance(embeddings, np.ndarray):
                return embeddings if embeddings.ndim == 1 else embeddings[0]
            else:
                return np.array(embeddings, dtype=np.float32)
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts."""
        if self.embedding_provider == "sentence_transformers":
            return self.embedding_model.encode(texts, convert_to_numpy=True, batch_size=settings.batch_size)
        elif self.embedding_provider == "fiservai":
            if not self.fiservai_client:
                raise ValueError("FiservAI client not initialized")
            embeddings, info = self.fiservai_client.__embed_batch(texts)
            # Convert to numpy array if needed
            if isinstance(embeddings, list):
                return np.array(embeddings, dtype=np.float32)
            elif isinstance(embeddings, np.ndarray):
                return embeddings
            else:
                return np.array(embeddings, dtype=np.float32)
        else:
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
    
    def search(self, query: str, top_k: int = None, filter_type: str = None) -> List[Dict]:
        """
        Search vector store for relevant documents.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filter_type: Filter by document type (html, feature, stepdef, pageobject)
        """
        if top_k is None:
            top_k = settings.top_k_retrieval
        
        query_embedding = self.embed_text(query)
        results = self.vector_store.search(query_embedding, top_k=top_k * 2)  # Get more for filtering
        
        # Filter by type if specified
        if filter_type:
            results = [r for r in results if r['metadata'].get('type') == filter_type]
        
        return results[:top_k]
    
    def _prepare_html_documents(self, parsed_elements: List[Dict]) -> List[Dict]:
        """Prepare HTML elements for vectorization."""
        documents = []
        for elem in parsed_elements:
            # Create searchable text
            text_parts = [
                f"UI Element: {elem['type']}",
                f"Text: {elem['text']}" if elem['text'] else "",
                f"ID: {elem['id']}" if elem['id'] else "",
                f"Placeholder: {elem['placeholder']}" if elem['placeholder'] else "",
                f"ARIA Label: {elem['aria_label']}" if elem['aria_label'] else "",
                f"Selector: {elem['preferred_selector']['method']}" if elem.get('preferred_selector') else "",
                f"Context: {elem['context']}" if elem['context'] else ""
            ]
            
            text = " | ".join([p for p in text_parts if p])
            
            documents.append({
                'text': text,
                'metadata': {
                    'element_type': elem['type'],
                    'element_id': elem.get('id', ''),
                    'selector_method': elem.get('preferred_selector', {}).get('method', ''),
                    'raw_element': json.dumps(elem)
                }
            })
        
        return documents
    
    def _prepare_feature_documents(self, parsed_data: Dict) -> List[Dict]:
        """Prepare feature file for vectorization."""
        documents = []
        
        # Vectorize each scenario with its steps
        for scenario in parsed_data.get('scenarios', []):
            text = f"Scenario: {scenario['title']}\n"
            text += "\n".join([f"{step['keyword']} {step['text']}" for step in scenario['steps']])
            
            documents.append({
                'text': text,
                'metadata': {
                    'scenario_title': scenario['title'],
                    'scenario_type': scenario['type'],
                    'step_count': len(scenario['steps'])
                }
            })
        
        # Vectorize unique steps separately for reuse
        for step in parsed_data.get('steps', []):
            documents.append({
                'text': f"{step['keyword']} {step['text']}",
                'metadata': {
                    'step_keyword': step['keyword'],
                    'step_normalized': step['normalized'],
                    'is_unique_step': True
                }
            })
        
        return documents
    
    def _prepare_stepdef_documents(self, parsed_data: Dict) -> List[Dict]:
        """Prepare step definitions for vectorization."""
        documents = []
        
        for step_def in parsed_data.get('step_definitions', []):
            text = f"Step Definition: {step_def['step_text']}\n"
            text += f"Method: {step_def['method_name']}\n"
            text += f"Implementation: {step_def['method_body']}"
            
            documents.append({
                'text': text,
                'metadata': {
                    'step_text': step_def['step_text'],
                    'step_normalized': step_def['normalized'],
                    'method_name': step_def['method_name'],
                    'full_definition': step_def['full_definition']
                }
            })
        
        return documents
    
    def _prepare_pageobject_documents(self, parsed_data: Dict) -> List[Dict]:
        """Prepare page object methods for vectorization."""
        documents = []
        
        # Vectorize each method
        for method in parsed_data.get('methods', []):
            text = f"Page Object Method: {method['name']}\n"
            text += f"Implementation: {method['body']}"
            
            documents.append({
                'text': text,
                'metadata': {
                    'method_name': method['name'],
                    'full_method': method['full_method']
                }
            })
        
        # Vectorize locators
        for locator in parsed_data.get('locators', []):
            documents.append({
                'text': f"WebElement Locator: {locator['element_name']}\n{locator['annotation']}",
                'metadata': {
                    'element_name': locator['element_name'],
                    'is_locator': True
                }
            })
        
        return documents
    
    def get_existing_steps(self) -> List[Dict]:
        """Retrieve all existing step definitions from vector store."""
        # Search with a generic query to get step definitions
        results = self.search("step definition", top_k=100, filter_type="stepdef")
        return results
    
    def find_similar_step(self, step_text: str, threshold: float = 0.85) -> Dict:
        """Find if a similar step already exists."""
        results = self.search(step_text, top_k=3, filter_type="stepdef")
        
        if results and results[0]['score'] >= threshold:
            return results[0]
        return None
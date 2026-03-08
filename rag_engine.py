"""
RAG Engine for Code-Sarthi
Manages document chunking, indexing in local FAISS vector store, and retrieval for context-aware explanations

This module implements the RAG (Retrieval-Augmented Generation) pipeline:
1. Text chunking: Splits PDF text into 500-1000 token segments
2. FAISS indexing: Stores chunks in local in-memory FAISS vector store
3. Titan Embeddings: Uses Amazon Titan Embeddings via Bedrock for vector generation
4. Metadata management: Tracks documents and chunks in local JSON
5. Context retrieval: Queries FAISS for relevant content using semantic search
"""

import json
import os
import re
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Callable
import boto3
from botocore.exceptions import ClientError
import numpy as np

# Try to import tiktoken for accurate token counting
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except ImportError:
    TIKTOKEN_AVAILABLE = False
    print("Warning: tiktoken not installed. Using approximate token counting.")

# Try to import FAISS for vector search
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("Warning: faiss-cpu not installed. Vector search will be unavailable.")


class RAGEngine:
    """
    Manages retrieval-augmented generation pipeline for Code-Sarthi
    
    Handles document chunking, FAISS indexing with Titan Embeddings, and context retrieval
    for lab manual content.
    """
    
    def __init__(
        self, 
        kendra_index_id: Optional[str] = None,
        region_name: str = "ap-northeast-1",
        metadata_file: str = "pdf_metadata.json",
        use_aws: bool = True,
        s3_bucket_name: str = "code-sarthi-pdfs-umang"
    ):
        """
        Initialize RAG Engine with FAISS + Titan Embeddings
        
        Args:
            kendra_index_id: Deprecated (kept for compatibility)
            region_name: AWS region for Bedrock
            metadata_file: Path to local JSON file for metadata storage
            use_aws: Whether to use AWS services (from USE_AWS env var)
            s3_bucket_name: S3 bucket name for document storage
        """
        self.region_name = region_name
        self.metadata_file = metadata_file
        self.use_aws = use_aws
        self.s3_bucket_name = s3_bucket_name
        
        # Ensure initialization never fails
        try:
            # Initialize AWS Bedrock client for embeddings (if AWS enabled)
            if self.use_aws:
                try:
                    self.bedrock_client = boto3.client('bedrock-runtime', region_name=region_name)
                except Exception as e:
                    print(f"Warning: Could not initialize Bedrock client: {e}")
                    self.bedrock_client = None
            else:
                self.bedrock_client = None
            
            # Initialize FAISS index (in-memory vector store)
            self.faiss_index = None
            self.chunk_store = []  # Store chunks with metadata
            self.embedding_dimension = 1536  # Titan Embeddings V1 dimension
            
            # Initialize tiktoken encoder if available
            if TIKTOKEN_AVAILABLE:
                try:
                    self.tokenizer = tiktoken.get_encoding("cl100k_base")  # GPT-4/Claude encoding
                except Exception:
                    self.tokenizer = None
            else:
                self.tokenizer = None
            
            # Load or initialize metadata
            self.metadata = self._load_metadata()
            
            # Initialize FAISS index if available
            if FAISS_AVAILABLE:
                self.faiss_index = faiss.IndexFlatL2(self.embedding_dimension)
            else:
                print("Warning: FAISS not available. Install faiss-cpu for vector search.")
                
        except Exception as e:
            # If anything fails, ensure object is still usable
            print(f"Warning: RAG Engine initialization had errors: {e}")
            self.bedrock_client = None
            self.faiss_index = None
            self.chunk_store = []
            self.embedding_dimension = 1536
            self.tokenizer = None
            self.metadata = {'documents': {}}
    
    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """
        Generate embedding using Amazon Titan Embeddings via Bedrock
        
        Args:
            text: Text to embed
            
        Returns:
            Numpy array of embedding vector or None if failed
        """
        if not self.use_aws or not self.bedrock_client:
            # Return mock embedding for local mode
            return np.random.rand(self.embedding_dimension).astype('float32')
        
        try:
            # Call Amazon Titan Embeddings V1 model
            # Model ID verified for us-west-2 region
            response = self.bedrock_client.invoke_model(
                modelId='amazon.titan-embed-text-v1',
                body=json.dumps({
                    "inputText": text
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            embedding = np.array(response_body['embedding'], dtype='float32')
            
            return embedding
            
        except Exception as e:
            print(f"Error generating embedding: {str(e)}")
            return None
    
    def chunk_text(
        self, 
        text: str, 
        chunk_size: int = 800,
        overlap: int = 100
    ) -> List[Dict[str, any]]:
        """
        Split text into semantic chunks of 500-1000 tokens
        
        Args:
            text: Extracted PDF text to chunk
            chunk_size: Target chunk size in tokens (default: 800)
            overlap: Token overlap between chunks (default: 100)
            
        Returns:
            List of chunk dictionaries with content and metadata
        """
        if not text or not text.strip():
            return []
        
        chunks = []
        
        # Split text into sentences (preserve sentence boundaries)
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        current_tokens = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)
            
            # If adding this sentence exceeds max size, save current chunk
            if current_tokens + sentence_tokens > 1000 and current_chunk:
                chunks.append({
                    'chunk_id': f"chunk_{chunk_index}",
                    'content': current_chunk.strip(),
                    'token_count': current_tokens,
                    'chunk_index': chunk_index
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + " " + sentence
                current_tokens = self._count_tokens(current_chunk)
                chunk_index += 1
            else:
                # Add sentence to current chunk
                current_chunk += " " + sentence
                current_tokens += sentence_tokens
            
            # If current chunk reaches target size, save it
            if current_tokens >= chunk_size:
                chunks.append({
                    'chunk_id': f"chunk_{chunk_index}",
                    'content': current_chunk.strip(),
                    'token_count': current_tokens,
                    'chunk_index': chunk_index
                })
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text
                current_tokens = self._count_tokens(current_chunk)
                chunk_index += 1
        
        # Add final chunk if it has content
        if current_chunk.strip():
            final_tokens = self._count_tokens(current_chunk)
            # Only add if it meets minimum size (500 tokens)
            if final_tokens >= 500:
                chunks.append({
                    'chunk_id': f"chunk_{chunk_index}",
                    'content': current_chunk.strip(),
                    'token_count': final_tokens,
                    'chunk_index': chunk_index
                })
        
        return chunks

    
    def index_document(
        self,
        document_id: str,
        document_name: str,
        text: str,
        user_id: str = "default_user",
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> Dict[str, any]:
        """
        Index a document in local FAISS vector store with Titan Embeddings
        
        Args:
            document_id: Unique document identifier
            document_name: Human-readable document name
            text: Extracted PDF text
            user_id: User identifier
            progress_callback: Optional callback(progress_percent, status_message)
            
        Returns:
            Dictionary with indexing results
        """
        try:
            # Step 1: Chunk text
            if progress_callback:
                progress_callback(10, "Chunking text...")
            
            chunks = self.chunk_text(text)
            
            if not chunks:
                return {
                    'status': 'error',
                    'message': 'No chunks generated from text'
                }
            
            # Step 2: Generate embeddings for chunks
            if progress_callback:
                progress_callback(30, f"Generating embeddings for {len(chunks)} chunks...")
            
            if not FAISS_AVAILABLE:
                # Store metadata locally without vector indexing
                self._store_metadata_locally(document_id, document_name, chunks, user_id)
                
                return {
                    'status': 'success',
                    'document_id': document_id,
                    'chunks_indexed': len(chunks),
                    'message': f'Document chunked successfully ({len(chunks)} chunks). FAISS not available.',
                    'faiss_indexed': False
                }
            
            # Generate embeddings and add to FAISS
            embeddings = []
            for i, chunk in enumerate(chunks):
                if progress_callback and i % 5 == 0:
                    progress = 30 + int((i / len(chunks)) * 50)
                    progress_callback(progress, f"Embedding chunk {i+1}/{len(chunks)}...")
                
                embedding = self._get_embedding(chunk['content'])
                if embedding is not None:
                    embeddings.append(embedding)
                    
                    # Store chunk with metadata
                    self.chunk_store.append({
                        'document_id': document_id,
                        'document_name': document_name,
                        'chunk_id': chunk['chunk_id'],
                        'chunk_index': chunk['chunk_index'],
                        'content': chunk['content'],
                        'token_count': chunk['token_count']
                    })
            
            # Step 3: Add embeddings to FAISS index
            if embeddings:
                if progress_callback:
                    progress_callback(80, "Indexing in FAISS...")
                
                embeddings_array = np.vstack(embeddings)
                self.faiss_index.add(embeddings_array)
            
            # Step 4: Store metadata locally
            if progress_callback:
                progress_callback(90, "Storing metadata...")
            
            self._store_metadata_locally(document_id, document_name, chunks, user_id)
            
            # Step 5: Complete
            if progress_callback:
                progress_callback(100, "Indexing complete!")
            
            return {
                'status': 'success',
                'document_id': document_id,
                'chunks_indexed': len(embeddings),
                'message': f'Successfully indexed {len(embeddings)} chunks in FAISS with Titan Embeddings',
                'faiss_indexed': True
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Indexing error: {str(e)}'
            }
    
    def retrieve(
        self, 
        query: str, 
        top_k: int = 5,
        relevance_threshold: float = 0.7
    ) -> List[Dict[str, any]]:
        """
        Retrieve relevant chunks for a query from FAISS using Titan Embeddings
        
        Args:
            query: Search query
            top_k: Number of results to return (default: 5)
            relevance_threshold: Minimum relevance score (default: 0.7)
            
        Returns:
            List of chunks with relevance scores and metadata
        """
        if not FAISS_AVAILABLE or self.faiss_index is None or self.faiss_index.ntotal == 0:
            return []
        
        try:
            # Generate embedding for query
            query_embedding = self._get_embedding(query)
            if query_embedding is None:
                return []
            
            # Search FAISS index
            query_embedding = query_embedding.reshape(1, -1)
            distances, indices = self.faiss_index.search(query_embedding, min(top_k, len(self.chunk_store)))
            
            # Process results
            results = []
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < 0 or idx >= len(self.chunk_store):
                    continue
                
                # Convert L2 distance to similarity score (0-1 range)
                similarity_score = float(np.exp(-distance / 10))
                
                # Filter by threshold
                if similarity_score >= relevance_threshold:
                    chunk = self.chunk_store[idx]
                    results.append({
                        'content': chunk['content'],
                        'relevance_score': similarity_score,
                        'document_id': chunk['document_id'],
                        'document_title': chunk['document_name'],
                        'chunk_index': chunk['chunk_index']
                    })
            
            return results[:top_k]
            
        except Exception as e:
            print(f"FAISS query error: {str(e)}")
            return []
    
    def should_use_rag(self, query: str) -> bool:
        """
        Heuristic function to determine if RAG should be used for a query
        
        Args:
            query: User query text
            
        Returns:
            True if RAG should be used, False otherwise
        """
        query_lower = query.lower()
        
        # Keywords that indicate RAG would be helpful
        rag_keywords = [
            'lab', 'assignment', 'manual', 'syllabus', 'experiment',
            'practical', 'exercise', 'tutorial', 'explain', 'what is',
            'how does', 'why', 'describe', 'definition', 'meaning',
            'purpose', 'documentation', 'reference', 'example', 'guide',
            'specification', 'requirement', 'according to', 'based on',
            'from the', 'in the manual', 'lecture', 'notes', 'chapter', 'section'
        ]
        
        # Check if any keyword is present
        for keyword in rag_keywords:
            if keyword in query_lower:
                return True
        
        # If query is very short (< 5 words), likely doesn't need RAG
        word_count = len(query.split())
        if word_count < 5:
            return False
        
        # If query contains code, might not need RAG
        code_indicators = ['def ', 'class ', 'function ', 'import ', 'for(', 'while(', '{', '}']
        has_code = any(indicator in query for indicator in code_indicators)
        if has_code and word_count < 10:
            return False
        
        # Default: use RAG for longer queries
        return word_count >= 10
    
    def get_document_metadata(self, document_id: str) -> Optional[Dict[str, any]]:
        """Get metadata for a specific document"""
        return self.metadata.get('documents', {}).get(document_id)
    
    def list_documents(self) -> List[Dict[str, any]]:
        """List all indexed documents"""
        return list(self.metadata.get('documents', {}).values())
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete a document and its chunks from FAISS and local metadata
        
        Args:
            document_id: Document identifier
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Remove chunks from chunk_store
            self.chunk_store = [
                chunk for chunk in self.chunk_store 
                if chunk['document_id'] != document_id
            ]
            
            # Rebuild FAISS index without deleted chunks
            if FAISS_AVAILABLE and self.chunk_store:
                self.faiss_index = faiss.IndexFlatL2(self.embedding_dimension)
                embeddings = []
                for chunk in self.chunk_store:
                    embedding = self._get_embedding(chunk['content'])
                    if embedding is not None:
                        embeddings.append(embedding)
                
                if embeddings:
                    embeddings_array = np.vstack(embeddings)
                    self.faiss_index.add(embeddings_array)
            
            # Remove from local metadata
            if document_id in self.metadata.get('documents', {}):
                del self.metadata['documents'][document_id]
                self._save_metadata()
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False
    
    # Private helper methods
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences preserving boundaries"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens accurately using tiktoken or fallback to approximation"""
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        else:
            return len(text) // 4
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """Get last N tokens of text for overlap"""
        overlap_chars = overlap_tokens * 4
        return text[-overlap_chars:] if len(text) > overlap_chars else text
    
    def _store_metadata_locally(
        self,
        document_id: str,
        document_name: str,
        chunks: List[Dict[str, any]],
        user_id: str
    ):
        """Store document metadata in local JSON file"""
        if 'documents' not in self.metadata:
            self.metadata['documents'] = {}
        
        self.metadata['documents'][document_id] = {
            'document_id': document_id,
            'document_name': document_name,
            'user_id': user_id,
            'upload_timestamp': datetime.now().isoformat(),
            'total_chunks': len(chunks),
            'chunk_ids': [chunk['chunk_id'] for chunk in chunks],
            'status': 'indexed'
        }
        
        self._save_metadata()
    
    def _load_metadata(self) -> Dict[str, any]:
        """Load metadata from JSON file"""
        if os.path.exists(self.metadata_file):
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading metadata: {str(e)}")
                return {'documents': {}}
        return {'documents': {}}
    
    def _save_metadata(self):
        """Save metadata to JSON file"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving metadata: {str(e)}")


# Convenience function for testing
def test_rag_engine():
    """Test RAG engine functionality"""
    engine = RAGEngine()
    
    # Test text
    test_text = """
    Python is a high-level programming language. It is widely used for web development.
    Python supports multiple programming paradigms. Object-oriented programming is one of them.
    Functions in Python are defined using the def keyword. Variables can store different types of data.
    """ * 50
    
    print("Testing RAG Engine...")
    print(f"Test text length: {len(test_text)} characters")
    
    # Test chunking
    chunks = engine.chunk_text(test_text)
    print(f"\nGenerated {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks[:3]):
        print(f"\nChunk {i}:")
        print(f"  Token count: {chunk['token_count']}")
        print(f"  Content preview: {chunk['content'][:100]}...")
    
    return chunks


if __name__ == "__main__":
    test_rag_engine()

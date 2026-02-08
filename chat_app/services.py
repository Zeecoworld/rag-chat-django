import cohere
from pinecone import Pinecone
from django.conf import settings
from typing import List, Tuple, Dict
import PyPDF2
import docx
import csv
import io


class DocumentProcessor:
    """Service for processing documents and managing embeddings"""
    
    def __init__(self):
        """Initialize Cohere and Pinecone clients"""
        try:
            # Initialize Cohere
            self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
            
            # Initialize Pinecone (NEW API)
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
            
            print("✅ DocumentProcessor initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize DocumentProcessor: {e}")
            raise
    
    def extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text from different file types"""
        try:
            if file_type == 'pdf':
                return self._extract_from_pdf(file_content)
            elif file_type in ['docx', 'doc']:
                return self._extract_from_docx(file_content)
            elif file_type == 'txt':
                return file_content.decode('utf-8')
            elif file_type == 'csv':
                return self._extract_from_csv(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            print(f"❌ Text extraction failed for {file_type}: {e}")
            raise
    
    def _extract_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF"""
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return text.strip()
    
    def _extract_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX"""
        doc_file = io.BytesIO(file_content)
        doc = docx.Document(doc_file)
        
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        
        return text.strip()
    
    def _extract_from_csv(self, file_content: bytes) -> str:
        """Extract text from CSV"""
        csv_file = io.StringIO(file_content.decode('utf-8'))
        csv_reader = csv.reader(csv_file)
        
        text = ""
        for row in csv_reader:
            text += " | ".join(row) + "\n"
        
        return text.strip()
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks"""
        if not text or not text.strip():
            raise ValueError("Cannot chunk empty text")
        
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk.strip():  # Only add non-empty chunks
                chunks.append(chunk)
        
        print(f"✅ Created {len(chunks)} chunks from text")
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using Cohere with improved error handling"""
        if not texts:
            raise ValueError("Cannot create embeddings for empty text list")
        
        # Filter out empty strings
        valid_texts = [text for text in texts if text and text.strip()]
        
        if not valid_texts:
            raise ValueError("All text chunks are empty")
        
        print(f"Creating embeddings for {len(valid_texts)} text chunks...")
        
        try:
            # Test Cohere API key first
            response = self.cohere_client.embed(
                texts=valid_texts,
                model='embed-english-v3.0',
                input_type='search_document',
                truncate='END'  # Truncate texts that are too long
            )
            
            if not response or not hasattr(response, 'embeddings'):
                raise Exception("Cohere API returned empty response")
            
            embeddings = response.embeddings
            
            if not embeddings or len(embeddings) == 0:
                raise Exception("Cohere API returned no embeddings")
            
            print(f"✅ Created {len(embeddings)} embeddings successfully")
            return embeddings
            
        except Exception as e:
            error_msg = str(e)
            
            # Check for common Cohere API errors
            if "api key" in error_msg.lower() or "unauthorized" in error_msg.lower():
                print(f"❌ Cohere API Key Error: {error_msg}")
                raise Exception("Invalid Cohere API key. Please check your settings.")
            elif "rate limit" in error_msg.lower():
                print(f"❌ Cohere Rate Limit: {error_msg}")
                raise Exception("Cohere API rate limit exceeded. Please try again later.")
            elif "list index out of range" in error_msg.lower():
                print(f"❌ Cohere API returned empty response. Possible causes:")
                print(f"   - Invalid API key")
                print(f"   - API quota exceeded")
                print(f"   - Network connectivity issue")
                raise Exception("Cohere API failed to generate embeddings. Please check your API key and quota.")
            else:
                print(f"❌ Cohere Embedding Error: {error_msg}")
                raise Exception(f"Failed to create embeddings: {error_msg}")
    
    def store_in_pinecone(self, chunks: List[str], embeddings: List[List[float]], 
                          namespace: str, metadata: Dict = None) -> List[str]:
        """Store embeddings in Pinecone"""
        try:
            vectors = []
            ids = []
            
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                vector_id = f"{namespace}_{i}"
                ids.append(vector_id)
                
                vector_metadata = {
                    'text': chunk,
                    'chunk_index': i,
                    **(metadata or {})
                }
                
                vectors.append({
                    'id': vector_id,
                    'values': embedding,
                    'metadata': vector_metadata
                })
            
            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
            
            print(f"✅ Stored {len(vectors)} vectors in Pinecone namespace: {namespace}")
            return ids
            
        except Exception as e:
            print(f"❌ Pinecone storage failed: {e}")
            raise
    
    def process_document(self, file_content: bytes, file_type: str, 
                        namespace: str, metadata: Dict = None) -> Tuple[List[str], List[str]]:
        """Complete document processing pipeline"""
        try:
            print(f"Starting document processing for file type: {file_type}")
            
            # 1. Extract text
            text = self.extract_text(file_content, file_type)
            print(f"✅ Extracted {len(text)} characters of text")
            
            if not text or len(text.strip()) < 10:
                raise ValueError("Document contains insufficient text content")
            
            # 2. Chunk text
            chunks = self.chunk_text(text)
            
            # 3. Create embeddings
            embeddings = self.create_embeddings(chunks)
            
            # 4. Store in Pinecone
            pinecone_ids = self.store_in_pinecone(chunks, embeddings, namespace, metadata)
            
            print(f"✅ Document processing complete: {len(chunks)} chunks, {len(pinecone_ids)} vectors")
            return chunks, pinecone_ids
            
        except Exception as e:
            print(f"❌ Document processing failed: {e}")
            raise
    
    def delete_document_vectors(self, namespace: str):
        """Delete all vectors for a document"""
        try:
            self.index.delete(delete_all=True, namespace=namespace)
            print(f"✅ Deleted vectors from namespace: {namespace}")
        except Exception as e:
            print(f"❌ Failed to delete vectors: {e}")
            raise


class ChatService:
    """Service for handling chat interactions"""
    
    def __init__(self):
        """Initialize Cohere and Pinecone clients"""
        try:
            self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
            
            # Initialize Pinecone (NEW API)
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)
            
            print("✅ ChatService initialized successfully")
            
        except Exception as e:
            print(f"❌ Failed to initialize ChatService: {e}")
            raise
    
    def retrieve_context(self, query: str, namespace: str, top_k: int = 3) -> List[str]:
        """Retrieve relevant context from Pinecone"""
        try:
            # Create query embedding
            query_response = self.cohere_client.embed(
                texts=[query],
                model='embed-english-v3.0',
                input_type='search_query'
            )
            
            query_embedding = query_response.embeddings[0]
            
            # Search in Pinecone
            results = self.index.query(
                vector=query_embedding,
                namespace=namespace,
                top_k=top_k,
                include_metadata=True
            )
            
            # Extract text chunks
            context_chunks = [match.metadata['text'] for match in results.matches]
            
            print(f"✅ Retrieved {len(context_chunks)} context chunks")
            return context_chunks
            
        except Exception as e:
            print(f"❌ Context retrieval failed: {e}")
            return []
    
    def generate_response(self, query: str, namespace: str, 
                         chat_history: List[Dict] = None) -> Tuple[str, List[str]]:
        """Generate response using RAG"""
        try:
            # Retrieve context
            context_chunks = self.retrieve_context(query, namespace)
            
            if not context_chunks:
                return "I couldn't find relevant information in the document to answer your question.", []
            
            # Build context
            context = "\n\n".join(context_chunks)
            
            # Build preamble
            preamble = f"""You are a helpful AI assistant. Answer the user's question based on the following context from their document.
            
Context:
{context}

If the answer is not in the context, say so politely."""
            
            # Generate response
            response = self.cohere_client.chat(
                message=query,
                chat_history=chat_history or [],
                preamble=preamble,
                model='command-r-plus-08-2024',
                temperature=0.3
            )
            
            return response.text, context_chunks
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            return f"Sorry, I encountered an error: {str(e)}", []
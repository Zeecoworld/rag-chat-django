import os
import cohere
from pinecone import Pinecone, ServerlessSpec
from django.conf import settings
import PyPDF2
import docx
import pandas as pd
from PIL import Image
import io
import uuid
from typing import List, Dict, Tuple


class DocumentProcessor:
    """Service to process documents, create embeddings, and store in Pinecone"""
    
    def __init__(self):
        self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
        
        # Initialize Pinecone
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Create or connect to index
        self.index_name = settings.PINECONE_INDEX_NAME
        self._initialize_index()
        
    def _initialize_index(self):
        """Initialize Pinecone index"""
        # Check if index exists
        existing_indexes = [index.name for index in self.pc.list_indexes()]
        
        if self.index_name not in existing_indexes:
            # Create index with Cohere embedding dimension (1024 for embed-english-v3.0)
            self.pc.create_index(
                name=self.index_name,
                dimension=1024,
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region=settings.PINECONE_ENVIRONMENT or 'us-east-1'
                )
            )
        
        self.index = self.pc.Index(self.index_name)
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        doc = docx.Document(io.BytesIO(file_content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    
    def extract_text_from_csv(self, file_content: bytes) -> str:
        """Extract text from CSV file"""
        df = pd.read_csv(io.BytesIO(file_content))
        # Convert dataframe to readable text format
        text = df.to_string(index=False)
        return text
    
    def extract_text_from_txt(self, file_content: bytes) -> str:
        """Extract text from TXT file"""
        return file_content.decode('utf-8')
    
    def extract_text_from_image(self, file_content: bytes) -> str:
        """
        For images, we'll return a placeholder.
        In production, you'd use OCR (like Tesseract) or vision APIs
        """
        try:
            image = Image.open(io.BytesIO(file_content))
            return f"[Image: {image.format}, Size: {image.size}]"
        except Exception as e:
            return f"[Image processing error: {str(e)}]"
    
    def extract_text(self, file_content: bytes, file_type: str) -> str:
        """Extract text based on file type"""
        extractors = {
            'pdf': self.extract_text_from_pdf,
            'docx': self.extract_text_from_docx,
            'doc': self.extract_text_from_docx,
            'csv': self.extract_text_from_csv,
            'txt': self.extract_text_from_txt,
            'image': self.extract_text_from_image,
        }
        
        extractor = extractors.get(file_type.lower())
        if not extractor:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        return extractor(file_content)
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into chunks with overlap"""
        words = text.split()
        chunks = []
        
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            if chunk:
                chunks.append(chunk)
        
        return chunks
    
    def create_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Create embeddings using Cohere"""
        response = self.cohere_client.embed(
            texts=texts,
            model='embed-english-v3.0',
            input_type='search_document'
        )
        return response.embeddings
    
    def store_in_pinecone(
        self, 
        embeddings: List[List[float]], 
        chunks: List[str],
        document_id: str,
        metadata: Dict = None
    ) -> List[str]:
        """Store embeddings in Pinecone"""
        vectors = []
        pinecone_ids = []
        
        for i, (embedding, chunk) in enumerate(zip(embeddings, chunks)):
            pinecone_id = f"{document_id}_chunk_{i}"
            pinecone_ids.append(pinecone_id)
            
            vector_metadata = {
                'text': chunk,
                'document_id': document_id,
                'chunk_index': i,
                **(metadata or {})
            }
            
            vectors.append({
                'id': pinecone_id,
                'values': embedding,
                'metadata': vector_metadata
            })
        
        # Upsert in batches
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch, namespace=document_id)
        
        return pinecone_ids
    
    def process_document(
        self, 
        file_content: bytes, 
        file_type: str, 
        document_id: str,
        metadata: Dict = None
    ) -> Tuple[List[str], List[str]]:
        """
        Full pipeline: extract text, chunk, embed, and store
        Returns: (chunks, pinecone_ids)
        """
        # Extract text
        text = self.extract_text(file_content, file_type)
        
        # Chunk text
        chunks = self.chunk_text(text)
        
        # Create embeddings
        embeddings = self.create_embeddings(chunks)
        
        # Store in Pinecone
        pinecone_ids = self.store_in_pinecone(
            embeddings, 
            chunks, 
            document_id,
            metadata
        )
        
        return chunks, pinecone_ids
    
    def search_similar(
        self, 
        query: str, 
        document_id: str, 
        top_k: int = 5
    ) -> List[Dict]:
        """Search for similar chunks in Pinecone"""
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
            top_k=top_k,
            namespace=document_id,
            include_metadata=True
        )
        
        return [
            {
                'id': match['id'],
                'score': match['score'],
                'text': match['metadata'].get('text', ''),
                'chunk_index': match['metadata'].get('chunk_index', 0)
            }
            for match in results['matches']
        ]
    
    def delete_document_vectors(self, document_id: str):
        """Delete all vectors for a document"""
        self.index.delete(namespace=document_id, delete_all=True)


class ChatService:
    """Service to handle chat interactions with documents"""
    
    def __init__(self):
        self.cohere_client = cohere.Client(settings.COHERE_API_KEY)
        self.doc_processor = DocumentProcessor()
    
    def generate_response(
        self, 
        query: str, 
        document_id: str, 
        chat_history: List[Dict] = None
    ) -> Tuple[str, List[Dict]]:
        """
        Generate a response using RAG
        Returns: (response_text, context_chunks)
        """
        # Search for relevant context
        context_chunks = self.doc_processor.search_similar(query, document_id)
        
        # Build context
        context = "\n\n".join([
            f"Context {i+1}: {chunk['text']}"
            for i, chunk in enumerate(context_chunks)
        ])
        
        # Build prompt
        prompt = f"""Based on the following context from the document, please answer the question.

Context:
{context}

Question: {query}

Answer:"""
        
        # Generate response using Cohere
        response = self.cohere_client.chat(
            message=prompt,
            model='command-r-08-2024',
            temperature=0.3,
            chat_history=chat_history or []
        )
        
        return response.text, context_chunks

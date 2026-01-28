# Django RAG Chat Application

A production-ready Django application that allows users to upload documents (PDF, DOCX, CSV, TXT, Images) and chat with them using RAG (Retrieval Augmented Generation) powered by Cohere embeddings, Pinecone vector database, and Cloudinary for file storage.

## Features

- 📁 **Document Upload**: Support for PDF, DOCX, CSV, TXT, and image files
- ☁️ **Cloud Storage**: Files stored securely on Cloudinary
- 🧠 **Smart Embeddings**: Cohere's embed-english-v3.0 for high-quality embeddings
- 🔍 **Vector Search**: Pinecone for fast and accurate similarity search
- 💬 **Intelligent Chat**: Context-aware responses using Cohere's Command-R-Plus
- 📊 **Document Processing**: Automatic text extraction and chunking
- 🎨 **Modern UI**: Beautiful, responsive interface with real-time chat
- 📝 **Chat History**: Persistent conversation storage

## Architecture

```
┌─────────────┐
│   User      │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Django    │
│   App       │
└──────┬──────┘
       │
       ├──────────────┐
       │              │
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│ Cloudinary  │  │   Cohere    │
│  (Storage)  │  │ (Embeddings)│
└─────────────┘  └─────────────┘
       │              │
       │              ▼
       │         ┌─────────────┐
       │         │  Pinecone   │
       │         │  (Vectors)  │
       │         └─────────────┘
       │              │
       └──────┬───────┘
              │
              ▼
        ┌─────────────┐
        │  PostgreSQL │
        │  (Metadata) │
        └─────────────┘
```

## Tech Stack

- **Backend**: Django 5.0
- **AI/ML**: Cohere (Embeddings & LLM)
- **Vector DB**: Pinecone
- **File Storage**: Cloudinary
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **Frontend**: Bootstrap 5, Vanilla JavaScript

## Prerequisites

Before you begin, ensure you have:

1. Python 3.10 or higher
2. API Keys for:
   - [Cohere](https://dashboard.cohere.ai/) - For embeddings and chat
   - [Pinecone](https://www.pinecone.io/) - For vector storage
   - [Cloudinary](https://cloudinary.com/) - For file storage

## Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd django-rag-chat
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```env
# Django Settings
SECRET_KEY=your-django-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Cohere API
COHERE_API_KEY=your-cohere-api-key

# Pinecone
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=us-east-1  # or your preferred region
PINECONE_INDEX_NAME=document-embeddings

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
```

### 5. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` in your browser.

## Getting API Keys

### Cohere

1. Go to [Cohere Dashboard](https://dashboard.cohere.ai/)
2. Sign up or log in
3. Navigate to API Keys section
4. Copy your API key

### Pinecone

1. Go to [Pinecone](https://www.pinecone.io/)
2. Sign up for a free account
3. Create a new project
4. Copy your API key from the console
5. Note your environment (e.g., `us-east-1`)

### Cloudinary

1. Go to [Cloudinary](https://cloudinary.com/)
2. Sign up for a free account
3. From your Dashboard, copy:
   - Cloud Name
   - API Key
   - API Secret

## Usage

### Uploading Documents

1. Navigate to the home page
2. Drag and drop a file or click to browse
3. Supported formats: PDF, DOCX, DOC, CSV, TXT, JPG, PNG
4. Wait for processing (automatic text extraction and embedding)

### Chatting with Documents

1. Click on any processed document
2. Type your question in the chat input
3. Get AI-powered answers based on document content
4. Chat history is automatically saved

### Example Questions

For a product manual:
- "What are the warranty terms?"
- "How do I reset the device?"
- "What are the technical specifications?"

For a research paper:
- "What is the main hypothesis?"
- "Summarize the methodology"
- "What were the key findings?"

## Project Structure

```
django-rag-chat/
├── chat_app/                    # Main Django app
│   ├── migrations/              # Database migrations
│   ├── templates/               # HTML templates
│   │   └── chat_app/
│   │       ├── base.html        # Base template
│   │       ├── index.html       # Document list
│   │       └── chat.html        # Chat interface
│   ├── models.py                # Database models
│   ├── views.py                 # View controllers
│   ├── urls.py                  # URL routing
│   ├── services.py              # Core RAG logic
│   ├── cloudinary_service.py    # File upload service
│   └── admin.py                 # Admin interface
├── rag_project/                 # Django project settings
│   ├── settings.py              # Configuration
│   ├── urls.py                  # Main URL routing
│   └── wsgi.py                  # WSGI config
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── manage.py                    # Django CLI
└── README.md                    # This file
```

## Key Components

### Models

- **Document**: Stores document metadata and Cloudinary URLs
- **DocumentChunk**: Individual text chunks with Pinecone IDs
- **ChatSession**: Chat conversation sessions
- **ChatMessage**: Individual messages with context

### Services

- **DocumentProcessor**: Handles text extraction, chunking, embedding, and vector storage
- **ChatService**: Manages RAG pipeline and response generation
- **CloudinaryService**: Handles file uploads and deletions

### API Endpoints

- `POST /upload/` - Upload a new document
- `GET /document/<id>/` - View document and chat interface
- `POST /chat/<session_id>/send/` - Send a chat message
- `GET /chat/<session_id>/history/` - Get chat history
- `DELETE /document/<id>/delete/` - Delete a document

## Configuration

### Chunk Size

Adjust in `chat_app/services.py`:

```python
def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50):
    # Modify chunk_size and overlap as needed
```

### Embedding Model

Change in `chat_app/services.py`:

```python
response = self.cohere_client.embed(
    texts=texts,
    model='embed-english-v3.0',  # Change model here
    input_type='search_document'
)
```

### Chat Model

Change in `chat_app/services.py`:

```python
response = self.cohere_client.chat(
    message=prompt,
    model='command-r-plus',  # Change model here
    temperature=0.3
)
```

## Production Deployment

### Security Checklist

- [ ] Set `DEBUG=False` in `.env`
- [ ] Use a strong `SECRET_KEY`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Set up proper CORS policies
- [ ] Use environment variables for all secrets
- [ ] Enable Django security middleware

### Recommended Services

- **Hosting**: AWS, Google Cloud, Heroku, DigitalOcean
- **Database**: PostgreSQL (Amazon RDS, Google Cloud SQL)
- **File Storage**: Keep using Cloudinary
- **Vector DB**: Pinecone (serverless)

### Environment Variables for Production

```env
DEBUG=False
SECRET_KEY=<strong-random-key>
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

DATABASE_URL=postgresql://user:password@host:5432/dbname
```

## Troubleshooting

### Document Processing Fails

- Check Cohere API key is valid
- Ensure Pinecone index exists and has correct dimensions (1024)
- Verify file format is supported

### Cloudinary Upload Errors

- Verify API credentials
- Check file size limits
- Ensure network connectivity

### Chat Responses Are Slow

- Consider using a smaller embedding model
- Reduce chunk size
- Implement caching for repeated queries

### Pinecone Connection Issues

- Verify API key and environment
- Check if index exists
- Ensure correct region is configured

## Advanced Features (Future)

- [ ] User authentication and document access control
- [ ] Multiple document search (cross-document chat)
- [ ] Document OCR for scanned PDFs
- [ ] Export chat history
- [ ] Voice input/output
- [ ] Multi-language support
- [ ] Document comparison
- [ ] Async processing with Celery

## Performance Optimization

1. **Caching**: Implement Redis for query caching
2. **Async Processing**: Use Celery for document processing
3. **CDN**: Serve static files via CDN
4. **Database Indexing**: Add indexes on frequently queried fields
5. **Connection Pooling**: Use pgBouncer for PostgreSQL

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Open a GitHub issue
- Check existing documentation
- Review Cohere, Pinecone, and Cloudinary docs

## Acknowledgments

- **Cohere** for powerful embeddings and LLM
- **Pinecone** for vector database
- **Cloudinary** for file storage
- **Django** community for excellent framework

---

Built with ❤️ using Django, Cohere, Pinecone, and Cloudinary

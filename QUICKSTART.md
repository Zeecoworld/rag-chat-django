# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your favorite editor
```

Required API keys:
- **Cohere**: Get from https://dashboard.cohere.ai/
- **Pinecone**: Get from https://www.pinecone.io/
- **Cloudinary**: Get from https://cloudinary.com/

### Step 3: Setup Database
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Test Configuration
```bash
python test_config.py
```

All tests should pass ✅

### Step 5: Run Server
```bash
python manage.py runserver
```

Visit http://localhost:8000

## Usage Flow

1. **Upload Document** → Drag & drop or click to upload
2. **Processing** → Automatic text extraction, chunking, and embedding
3. **Chat** → Click on document to start chatting
4. **Ask Questions** → Get AI-powered answers based on document content

## Common Commands

```bash
# Create superuser for admin access
python manage.py createsuperuser

# Access admin panel
http://localhost:8000/admin

# Run tests
python test_config.py

# Collect static files (production)
python manage.py collectstatic
```

## Troubleshooting

### "No module named X"
```bash
pip install -r requirements.txt
```

### "API Key Error"
- Check .env file has correct keys
- Verify keys are valid on respective platforms

### "Pinecone Index Error"
- Index is created automatically on first upload
- Ensure PINECONE_INDEX_NAME is set in .env

### "Cloudinary Upload Failed"
- Verify all three Cloudinary credentials
- Check file size (max 10MB)

## File Types Supported

- ✅ PDF (.pdf)
- ✅ Word Documents (.docx, .doc)
- ✅ CSV (.csv)
- ✅ Text Files (.txt)
- ✅ Images (.jpg, .jpeg, .png)

## Architecture Overview

```
User Upload → Cloudinary (Storage)
           → Text Extraction
           → Chunking
           → Cohere (Embeddings)
           → Pinecone (Vector DB)

User Query → Cohere (Query Embedding)
          → Pinecone (Similarity Search)
          → Cohere (Response Generation)
          → User sees answer
```

## API Endpoints

- `GET /` - Home page with document list
- `POST /upload/` - Upload new document
- `GET /document/<id>/` - Chat interface
- `POST /chat/<session_id>/send/` - Send message
- `DELETE /document/<id>/delete/` - Delete document

## Next Steps

- Add user authentication
- Implement async processing with Celery
- Add more file type support
- Enable multi-document search
- Export chat history

## Need Help?

- Check README.md for detailed documentation
- Review error messages in terminal
- Test API connections with test_config.py
- Check Django admin panel for data issues

---

Happy chatting! 🚀

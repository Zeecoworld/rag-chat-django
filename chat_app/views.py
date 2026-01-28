from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db import transaction
from .models import Document, DocumentChunk, ChatSession, ChatMessage
from .services import DocumentProcessor, ChatService
from .cloudinary_service import CloudinaryService
from django.conf import settings
import json


def index(request):
    """Main page showing all documents"""
    documents = Document.objects.all()
    return render(request, 'chat_app/index.html', {
        'documents': documents
    })


@require_http_methods(["POST"])
def upload_document(request):
    try:
        if 'file' not in request.FILES:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        file = request.FILES['file']
        
        # 1. Validation
        if file.size > settings.MAX_UPLOAD_SIZE:
            return JsonResponse({
                'error': f'File too large. Max size is {settings.MAX_UPLOAD_SIZE / (1024*1024)}MB'
            }, status=400)
        
        file_extension = file.name.split('.')[-1].lower()
        if file_extension not in settings.ALLOWED_FILE_TYPES:
            return JsonResponse({
                'error': f'File type not allowed. Allowed types: {", ".join(settings.ALLOWED_FILE_TYPES)}'
            }, status=400)

        # 2. External Upload (Cloudinary)
        cloudinary_service = CloudinaryService()
        cloudinary_url, public_id = cloudinary_service.upload_file(file)
        
        try:
            with transaction.atomic():
                document = Document.objects.create(
                    title=file.name,
                    file_type=file_extension,
                    cloudinary_url=cloudinary_url,
                    cloudinary_public_id=public_id,
                    file_size=file.size
                )
                
                document.pinecone_namespace = str(document.id)
                document.save()

                file.seek(0)
                file_content = file.read()
                
                doc_processor = DocumentProcessor()
                chunks, pinecone_ids = doc_processor.process_document(
                    file_content,
                    file_extension,
                    document.pinecone_namespace,
                    metadata={
                        'title': document.title,
                        'file_type': document.file_type
                    }
                )
                
                for i, (chunk_text, pinecone_id) in enumerate(zip(chunks, pinecone_ids)):
                    DocumentChunk.objects.create(
                        document=document,
                        chunk_index=i,
                        text_content=chunk_text,
                        pinecone_id=pinecone_id
                    )
                
                # Final updates
                document.processed = True
                document.processed_at = timezone.now()
                document.chunk_count = len(chunks)
                document.save()

            return JsonResponse({
                'success': True,
                'document': {
                    'id': str(document.id),
                    'title': document.title,
                    'file_type': document.file_type,
                    'chunk_count': document.chunk_count,
                    'url': cloudinary_url
                }
            })

        except Exception as e:
            cloudinary_service.delete_file(public_id)
            raise e

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def document_detail(request, document_id):
    document = get_object_or_404(Document, id=document_id)
    
    # Get or create a chat session
    chat_session = ChatSession.objects.filter(document=document).first()
    if not chat_session:
        chat_session = ChatSession.objects.create(
            document=document,
            title=f"Chat with {document.title}"
        )
    
    messages = chat_session.messages.all()
    
    return render(request, 'chat_app/chat.html', {
        'document': document,
        'session': chat_session,
        'messages': messages
    })


@require_http_methods(["POST"])
def send_message(request, session_id):
    try:
        session = get_object_or_404(ChatSession, id=session_id)
        
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)
        
        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session,
            role='user',
            content=user_message
        )
        
        # Get chat history
        previous_messages = session.messages.filter(
            created_at__lt=user_msg.created_at
        ).order_by('created_at')[:10]
        
        role_map = {
            'user': 'USER',
            'assistant': 'CHATBOT'
        }
        
        chat_history = [
            {
                'role': role_map.get(msg.role, 'USER'), 
                'message': msg.content
            }
            for msg in previous_messages
        ]
        
        # Generate response
        chat_service = ChatService()
        response_text, context_chunks = chat_service.generate_response(
            user_message,
            str(session.document.id),
            chat_history
        )
        
        # Save assistant message (keep 'assistant' for your DB internal logic)
        assistant_msg = ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=response_text,
            context_chunks=context_chunks
        )
        
        session.updated_at = timezone.now()
        session.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': str(assistant_msg.id),
                'role': 'assistant',
                'content': response_text,
                'created_at': assistant_msg.created_at.isoformat()
            },
            'context_chunks': context_chunks
        })
    
    except Exception as e:
        if "Invalid role" in str(e):
            return JsonResponse({'error': f'AI Service Role Error: {str(e)}'}, status=400)
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["DELETE"])
def delete_document(request, document_id):
    try:
        document = get_object_or_404(Document, id=document_id)
        
        # Delete from Pinecone
        doc_processor = DocumentProcessor()
        doc_processor.delete_document_vectors(str(document.id))
        
        # Delete from Cloudinary
        cloudinary_service = CloudinaryService()
        cloudinary_service.delete_file(document.cloudinary_public_id)
        
        # Delete from database
        document.delete()
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def get_chat_history(request, session_id):
    session = get_object_or_404(ChatSession, id=session_id)
    messages = session.messages.all()
    
    return JsonResponse({
        'messages': [
            {
                'id': str(msg.id),
                'role': msg.role,
                'content': msg.content,
                'created_at': msg.created_at.isoformat()
            }
            for msg in messages
        ]
    })

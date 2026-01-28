from django.contrib import admin
from .models import Document, DocumentChunk, ChatSession, ChatMessage


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'file_type', 'file_size', 'processed', 'chunk_count', 'uploaded_at']
    list_filter = ['file_type', 'processed', 'uploaded_at']
    search_fields = ['title', 'cloudinary_public_id']
    readonly_fields = ['id', 'uploaded_at', 'processed_at']


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ['document', 'chunk_index', 'pinecone_id']
    list_filter = ['document']
    search_fields = ['text_content', 'pinecone_id']


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'document', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['title']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content']
    readonly_fields = ['id', 'created_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content'

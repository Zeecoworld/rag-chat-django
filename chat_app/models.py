from django.db import models
from django.contrib.auth.models import User
import uuid


class Document(models.Model):
    """Model to store uploaded documents"""
    FILE_TYPES = (
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('csv', 'CSV'),
        ('txt', 'Text File'),
        ('image', 'Image'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents', null=True, blank=True)
    title = models.CharField(max_length=255)
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    cloudinary_url = models.URLField(max_length=500)
    cloudinary_public_id = models.CharField(max_length=255)
    file_size = models.IntegerField(help_text="File size in bytes")
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    chunk_count = models.IntegerField(default=0)
    
    # Pinecone metadata
    pinecone_namespace = models.CharField(max_length=255, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['user', '-uploaded_at']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.file_type})"


class DocumentChunk(models.Model):
    """Model to store document chunks for better tracking"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.IntegerField()
    text_content = models.TextField()
    pinecone_id = models.CharField(max_length=255, unique=True)
    
    class Meta:
        ordering = ['chunk_index']
        unique_together = ['document', 'chunk_index']
    
    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"


class ChatSession(models.Model):
    """Model to store chat sessions"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions', null=True, blank=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"Chat: {self.title}"


class ChatMessage(models.Model):
    """Model to store individual chat messages"""
    ROLE_CHOICES = (
        ('user', 'User'),
        ('assistant', 'Assistant'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # Context used for this message
    context_chunks = models.JSONField(default=list, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

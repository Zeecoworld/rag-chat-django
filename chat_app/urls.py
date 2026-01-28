from django.urls import path
from . import views

app_name = 'chat_app'

urlpatterns = [
    path('', views.index, name='index'),
    path('upload/', views.upload_document, name='upload_document'),
    path('document/<uuid:document_id>/', views.document_detail, name='document_detail'),
    path('chat/<uuid:session_id>/send/', views.send_message, name='send_message'),
    path('chat/<uuid:session_id>/history/', views.get_chat_history, name='chat_history'),
    path('document/<uuid:document_id>/delete/', views.delete_document, name='delete_document'),
]

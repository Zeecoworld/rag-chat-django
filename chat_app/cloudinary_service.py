import cloudinary
import cloudinary.uploader
from django.conf import settings
from typing import Dict, Tuple
import os


class CloudinaryService:
    
    def __init__(self):
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET
        )
    
    def upload_file(self, file, folder: str = "documents") -> Tuple[str, str]:
        # Determine resource type
        file_extension = file.name.split('.')[-1].lower()
        
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            resource_type = 'image'
        elif file_extension in ['docx','pdf']:
            resource_type = 'document' 
        else:
            resource_type = 'raw'
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file,
            folder=folder,
            resource_type=resource_type,
            use_filename=True,
            unique_filename=True
        )
        
        return upload_result['secure_url'], upload_result['public_id']
    
    def delete_file(self, public_id: str, resource_type: str = 'raw') -> bool:
        """Delete file from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type
            )
            return result.get('result') == 'ok'
        except Exception as e:
            print(f"Error deleting from Cloudinary: {e}")
            return False
    
    def get_file_url(self, public_id: str, resource_type: str = 'raw') -> str:
        """Get secure URL for a file"""
        return cloudinary.CloudinaryImage(public_id).build_url(
            resource_type=resource_type,
            secure=True
        )

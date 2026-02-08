import cloudinary
import cloudinary.uploader
from django.conf import settings
from typing import Dict, Tuple
import os


class CloudinaryService:
    
    def __init__(self):
        """Initialize Cloudinary configuration"""
        try:
            cloudinary.config(
                cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                api_key=settings.CLOUDINARY_API_KEY,
                api_secret=settings.CLOUDINARY_API_SECRET
            )
        except AttributeError as e:
            raise Exception(f"Cloudinary settings missing: {e}. Please check your settings.py")
    
    def get_resource_type(self, file_extension: str) -> str:
        """Determine Cloudinary resource type based on file extension"""
        file_extension = file_extension.lower()
        
        if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp', 'svg']:
            return 'image'
        elif file_extension in ['pdf', 'docx', 'doc']:
            return 'raw'  # Changed from 'document' to 'raw'
        else:
            return 'raw'
    
    def upload_file(self, file, folder: str = "documents") -> Tuple[str, str, str]:
        """
        Upload file to Cloudinary
        Returns: (secure_url, public_id, resource_type)
        """
        try:
            # Determine resource type
            file_extension = file.name.split('.')[-1].lower()
            resource_type = self.get_resource_type(file_extension)
            
            print(f"Uploading {file.name} as resource_type: {resource_type}")
            
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(
                file,
                folder=folder,
                resource_type=resource_type,
                use_filename=True,
                unique_filename=True
            )
            
            return (
                upload_result['secure_url'], 
                upload_result['public_id'],
                resource_type
            )
            
        except Exception as e:
            print(f"Cloudinary upload error: {str(e)}")
            raise Exception(f"Failed to upload to Cloudinary: {str(e)}")
    
    def delete_file(self, public_id: str, resource_type: str = 'raw') -> bool:
        """Delete file from Cloudinary"""
        try:
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type,
                invalidate=True  # Invalidate CDN cache
            )
            
            print(f"Delete result for {public_id}: {result}")
            return result.get('result') == 'ok'
            
        except Exception as e:
            print(f"Error deleting from Cloudinary: {e}")
            return False
    
    def get_file_url(self, public_id: str, resource_type: str = 'raw') -> str:
        """Get secure URL for a file"""
        try:
            return cloudinary.CloudinaryImage(public_id).build_url(
                resource_type=resource_type,
                secure=True
            )
        except Exception as e:
            print(f"Error generating URL: {e}")
            return ""
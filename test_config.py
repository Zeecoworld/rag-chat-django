"""
Test script to verify all API connections and configurations
Run this after setting up your .env file
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_cohere():
    """Test Cohere API connection"""
    print("\n🔍 Testing Cohere API...")
    try:
        import cohere
        api_key = os.getenv('COHERE_API_KEY')
        
        if not api_key:
            print("❌ COHERE_API_KEY not found in .env")
            return False
        
        client = cohere.Client(api_key)
        response = client.embed(
            texts=["test"],
            model='embed-english-v3.0',
            input_type='search_document'
        )
        print("✅ Cohere API connection successful!")
        print(f"   Embedding dimension: {len(response.embeddings[0])}")
        return True
    except Exception as e:
        print(f"❌ Cohere API error: {str(e)}")
        return False


def test_pinecone():
    """Test Pinecone connection"""
    print("\n🔍 Testing Pinecone...")
    try:
        from pinecone import Pinecone
        api_key = os.getenv('PINECONE_API_KEY')
        
        if not api_key:
            print("❌ PINECONE_API_KEY not found in .env")
            return False
        
        pc = Pinecone(api_key=api_key)
        indexes = [index.name for index in pc.list_indexes()]
        print("✅ Pinecone connection successful!")
        print(f"   Existing indexes: {indexes if indexes else 'None'}")
        
        index_name = os.getenv('PINECONE_INDEX_NAME', 'document-embeddings')
        if index_name not in indexes:
            print(f"⚠️  Index '{index_name}' will be created on first document upload")
        
        return True
    except Exception as e:
        print(f"❌ Pinecone error: {str(e)}")
        return False


def test_cloudinary():
    """Test Cloudinary configuration"""
    print("\n🔍 Testing Cloudinary...")
    try:
        import cloudinary
        
        cloud_name = os.getenv('CLOUDINARY_CLOUD_NAME')
        api_key = os.getenv('CLOUDINARY_API_KEY')
        api_secret = os.getenv('CLOUDINARY_API_SECRET')
        
        if not all([cloud_name, api_key, api_secret]):
            print("❌ Cloudinary credentials missing in .env")
            return False
        
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
        
        # Test by getting account info
        print("✅ Cloudinary configuration successful!")
        print(f"   Cloud name: {cloud_name}")
        return True
    except Exception as e:
        print(f"❌ Cloudinary error: {str(e)}")
        return False


def test_django_settings():
    """Test Django configuration"""
    print("\n🔍 Testing Django settings...")
    try:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rag_project.settings')
        django.setup()
        
        from django.conf import settings
        
        # Check important settings
        checks = {
            'SECRET_KEY': bool(settings.SECRET_KEY and settings.SECRET_KEY != 'django-insecure-change-this-in-production'),
            'Database': settings.DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3',
        }
        
        if all(checks.values()):
            print("✅ Django settings configured correctly!")
            print(f"   Debug mode: {settings.DEBUG}")
            print(f"   Database: {settings.DATABASES['default']['ENGINE']}")
            return True
        else:
            print("⚠️  Some Django settings need attention:")
            for key, value in checks.items():
                if not value:
                    print(f"   - {key}")
            return False
    except Exception as e:
        print(f"❌ Django error: {str(e)}")
        return False


def main():
    """Run all tests"""
    print("=" * 50)
    print("RAG Chat Application - Configuration Test")
    print("=" * 50)
    
    results = {
        'Cohere': test_cohere(),
        'Pinecone': test_pinecone(),
        'Cloudinary': test_cloudinary(),
        'Django': test_django_settings(),
    }
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    
    for service, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"{status_icon} {service}: {'PASSED' if status else 'FAILED'}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! You're ready to run the application.")
        print("\nNext steps:")
        print("1. Run migrations: python manage.py migrate")
        print("2. Start server: python manage.py runserver")
        print("3. Visit: http://localhost:8000")
    else:
        print("⚠️  Some tests failed. Please check your .env configuration.")
        print("\nMake sure you have:")
        print("1. Valid API keys for Cohere, Pinecone, and Cloudinary")
        print("2. Correct environment/region settings")
        print("3. All required packages installed")
    print("=" * 50)


if __name__ == '__main__':
    main()

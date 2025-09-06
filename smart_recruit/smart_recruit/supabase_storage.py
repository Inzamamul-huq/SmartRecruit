import mimetypes
import uuid
from datetime import timedelta
from django.utils import timezone
from .supabase_client import get_supabase

BUCKET_NAME = "resumes"


def upload_file(file_obj, path_prefix: str) -> dict:
    """
    Upload a file-like object to Supabase Storage.
    
    Args:
        file_obj: File object or file-like object to upload
        path_prefix: Prefix for the file path (e.g., 'students/1')
        
    Returns:
        dict with keys: path, public_url, signed_url
    """
    supabase = get_supabase()

    
    ext = ''
    original_name = getattr(file_obj, 'name', 'file')
    
    
    if '.' in original_name:
        ext = '.' + original_name.split('.')[-1].lower()
    else:
        guess = mimetypes.guess_extension(mimetypes.guess_type(original_name)[0] or '')
        if guess:
            ext = guess.lower()
    
    
    filename = f"{uuid.uuid4().hex}{ext}"
    
    
    path_prefix = path_prefix.strip('/')
    path = f"{path_prefix}/{filename}" if path_prefix else filename

    
    data = file_obj.read()
    try:
        file_obj.seek(0)
    except Exception:
        pass

    
    try:
        
        buckets = supabase.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        
        
        if BUCKET_NAME not in bucket_names:
            supabase.storage.create_bucket(
                BUCKET_NAME,
                public=True,
                file_size_limit=1024 * 1024 * 5,  
                allowed_mime_types=['application/pdf', 'application/msword', 
                                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            )
            
            
            supabase.storage.get_bucket(BUCKET_NAME).make_public()
    except Exception as e:
        print(f"Warning: Could not create bucket - {str(e)}")

    
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    try:
        
        supabase.storage.from_(BUCKET_NAME).upload(
            path,
            data,
            {
                'content-type': content_type,
                'cache-control': 'public, max-age=31536000', 
                'x-upsert': 'false'
            }
        )
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        raise

    
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(path)

    
    expires_in = int(timedelta(days=365).total_seconds())
    signed_resp = supabase.storage.from_(BUCKET_NAME).create_signed_url(path, expires_in)
    signed_url = signed_resp.get('signedURL') if isinstance(signed_resp, dict) else signed_resp

    return {'path': path, 'public_url': public_url, 'signed_url': signed_url}

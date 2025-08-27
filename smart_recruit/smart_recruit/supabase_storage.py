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

    # Generate a unique filename
    ext = ''
    original_name = getattr(file_obj, 'name', 'file')
    
    # Get file extension
    if '.' in original_name:
        ext = '.' + original_name.split('.')[-1].lower()
    else:
        guess = mimetypes.guess_extension(mimetypes.guess_type(original_name)[0] or '')
        if guess:
            ext = guess.lower()
    
    # Create a clean filename with UUID and original extension
    filename = f"{uuid.uuid4().hex}{ext}"
    
    # Normalize path (remove leading/trailing slashes)
    path_prefix = path_prefix.strip('/')
    path = f"{path_prefix}/{filename}" if path_prefix else filename

    # Read bytes
    data = file_obj.read()
    try:
        file_obj.seek(0)
    except Exception:
        pass

    # Ensure bucket exists (ignore if already exists)
    try:
        # Get all buckets
        buckets = supabase.storage.list_buckets()
        bucket_names = [bucket.name for bucket in buckets]
        
        # Create bucket if it doesn't exist
        if BUCKET_NAME not in bucket_names:
            supabase.storage.create_bucket(
                BUCKET_NAME,
                public=True,
                file_size_limit=1024 * 1024 * 5,  # 5MB
                allowed_mime_types=['application/pdf', 'application/msword', 
                                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
            )
            
            # Set bucket policy to public
            supabase.storage.get_bucket(BUCKET_NAME).make_public()
    except Exception as e:
        print(f"Warning: Could not create bucket - {str(e)}")

    # Upload file with proper content type
    content_type = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    try:
        # First try to upload the file
        supabase.storage.from_(BUCKET_NAME).upload(
            path,
            data,
            {
                'content-type': content_type,
                'cache-control': 'public, max-age=31536000',  # Cache for 1 year
                'x-upsert': 'false'
            }
        )
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        raise

    # Public URL
    public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(path)

    # Signed URL (1 year)
    expires_in = int(timedelta(days=365).total_seconds())
    signed_resp = supabase.storage.from_(BUCKET_NAME).create_signed_url(path, expires_in)
    signed_url = signed_resp.get('signedURL') if isinstance(signed_resp, dict) else signed_resp

    return {'path': path, 'public_url': public_url, 'signed_url': signed_url}

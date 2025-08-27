from supabase import create_client, Client
from django.conf import settings

_supabase_client: Client | None = None


def get_supabase() -> Client:
    global _supabase_client
    if _supabase_client is None:
        url = settings.SUPABASE_URL
        key = settings.SUPABASE_SERVICE_ROLE_KEY
        if not url or not key:
            raise RuntimeError("Supabase URL or Service Role Key is not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY in environment.")
        _supabase_client = create_client(url, key)
    return _supabase_client

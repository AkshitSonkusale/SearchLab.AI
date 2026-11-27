import os
import sys
from supabase import create_client, Client

sys.path.insert(0, os.path.dirname(__file__))
from app.config import get_settings

def init_bucket():
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        print("Supabase URL or Service Key not configured, skipping bucket check.")
        return

    print("Connecting to Supabase Storage API...")
    client: Client = create_client(settings.supabase_url, settings.supabase_service_key)
    buckets = client.storage.list_buckets()
    bucket_names = [b.name for b in buckets]
    print(f"Existing buckets: {bucket_names}")

    if settings.supabase_storage_bucket not in bucket_names:
        print(f"Creating private bucket '{settings.supabase_storage_bucket}'...")
        client.storage.create_bucket(
            settings.supabase_storage_bucket,
            options={"public": False}
        )
        print(f"Bucket '{settings.supabase_storage_bucket}' created successfully!")
    else:
        print(f"Bucket '{settings.supabase_storage_bucket}' already exists.")

if __name__ == "__main__":
    init_bucket()

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

try:
    supabase: Client = create_client(url, key)
    print("Testing 'students' count query...")
    res = supabase.table('students').select('*', count='exact').eq('active_status', 1).execute()
    print("Count:", res.count)
    print("Data sample:", res.data[:2])
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")

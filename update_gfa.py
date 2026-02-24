import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

print("Updating Supabase database...")
res = supabase.table('settings').update({
    'school_name': 'Glorious Future Academy',
    'logo_path': 'gfa_logo.png'
}).eq('id', 1).execute()

print("Settings updated:", res.data)

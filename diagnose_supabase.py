import os
import httpx
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

print(f"Testing connection to: {url}")
print(f"Key preview: {key[:15]}...")

try:
    # 1. Test basic network connectivity to the URL
    hostname = url.replace("https://", "").split("/")[0]
    print(f"Pinging {hostname}...")
    
    # Use httpx directly to see raw connection issues
    with httpx.Client() as client:
        response = client.get(f"{url}/rest/v1/", headers={"apikey": key})
        print(f"Raw HTTP Response: {response.status_code}")
        print(f"Response Content: {response.text}")

    # 2. Test using Supabase SDK
    supabase: Client = create_client(url, key)
    # Just try to get something small
    res = supabase.table('settings').select('*').limit(1).execute()
    print("SDK Success:", res.data)

except httpx.ConnectError as e:
    print(f"Connection Error: {e}")
    print("This often happens due to firewall, proxy, or local network blocking the request.")
except Exception as e:
    print(f"An error occurred: {type(e).__name__}: {e}")

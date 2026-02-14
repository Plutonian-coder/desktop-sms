import httpx

try:
    print("Testing API: /scores/api/students_in_class/1")
    # Assuming the app is running (which it is, background process)
    # Note: run.py runs on port 5000.
    
    # We can try to hit the local server.
    # If the user has it running in the background from previous 'run_command', 
    # we can access it.
    
    # Wait, the 'run_command' output showed "Running on http://127.0.0.1:5000".
    
    resp = httpx.get("http://127.0.0.1:5000/scores/api/students_in_class/1")
    print(f"Status Code: {resp.status_code}")
    print(f"Response: {resp.text}")
    print(f"JSON Valid: {resp.json()}")

except Exception as e:
    print(f"Error: {e}")

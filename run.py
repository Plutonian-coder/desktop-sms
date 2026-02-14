"""
Flask Application Entry Point
"""
from app import create_app
from dotenv import load_dotenv

load_dotenv()

app = create_app()

if __name__ == '__main__':
    # usage_reloader=False prevents "WinError 10054" with Supabase on Windows
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)

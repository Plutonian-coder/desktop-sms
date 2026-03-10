"""
Flask Application Entry Point
"""
import sys
import os

# PyInstaller frozen-app support: set working directory to the exe's folder
# so that templates, static files, and data/ resolve correctly.
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

from app import create_app

app = create_app()

if __name__ == '__main__':
    is_frozen = getattr(sys, 'frozen', False)
    app.run(
        debug=not is_frozen,
        host='127.0.0.1',
        port=5000,
        use_reloader=False,
    )

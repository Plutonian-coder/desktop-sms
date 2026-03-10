"""
Flask Application Factory
"""
from flask import Flask, session, redirect, url_for, request
import os
import sys
from datetime import timedelta
from flask_cors import CORS

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)

    # CORS — restrict to localhost origins only (Electron + dev browser)
    allowed_origins = [
        'http://localhost:5000',
        'http://127.0.0.1:5000',
    ]
    CORS(app, origins=allowed_origins)

    # Configuration
    app.config['SECRET_KEY'] = 'yabatech-jss-v2-8f3a9c7d2e1b4a6f5d0e3c2b1a9f8e7d'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)

    # Resolve database path (frozen-app aware)
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.dirname(__file__))
    app.config['DATABASE_PATH'] = os.path.join(base, 'data', 'school.db')

    # Ensure src/ is on the path so blueprints can import database.db_manager
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

    # Initialise SQLite schema (creates tables if they don't exist yet)
    from database.db_manager import DatabaseManager
    _db = DatabaseManager()
    _db.initialize_database()

    # Register blueprints
    from app.routes import main, students, sessions, subjects, scores, attendance, reports, auth, fees, exports

    app.register_blueprint(auth.bp)   # auth first
    app.register_blueprint(main.bp)
    app.register_blueprint(students.bp)
    app.register_blueprint(sessions.bp)
    app.register_blueprint(subjects.bp)
    app.register_blueprint(scores.bp)
    app.register_blueprint(attendance.bp)
    app.register_blueprint(reports.bp)
    app.register_blueprint(fees.bp)
    app.register_blueprint(exports.bp)

    # Authentication middleware
    @app.before_request
    def check_authentication():
        """Redirect to login if not authenticated"""
        if request.endpoint and (
            request.endpoint.startswith('auth.') or
            request.endpoint == 'static'
        ):
            return None
        if 'user' not in session:
            return redirect(url_for('auth.login'))

    # Inject school settings into every template
    @app.context_processor
    def inject_school_settings():
        try:
            rows = _db.execute_query('SELECT * FROM settings WHERE id = 1')
            return {'school_settings': rows[0] if rows else {}}
        except Exception:
            return {'school_settings': {}}

    return app

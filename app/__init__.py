"""
Flask Application Factory
"""
from flask import Flask, session, redirect, url_for, request
import os
from datetime import timedelta
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    
    # CORS — restrict to known origins
    allowed_origins = os.getenv('ALLOWED_ORIGINS', 'http://localhost:5000').split(',')
    CORS(app, origins=allowed_origins)
    
    # Configuration — secret key from environment
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-dev-key-change-in-production')
    app.config['DATABASE_PATH'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'school.db')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts 7 days
    
    # Register blueprints
    from app.routes import main, students, sessions, subjects, scores, attendance, reports, auth, fees, exports
    
    app.register_blueprint(auth.bp)  # Register auth first
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
        # Allow access to auth routes and static files
        if request.endpoint and (
            request.endpoint.startswith('auth.') or 
            request.endpoint == 'static'
        ):
            return None
        
        # Check if user is logged in
        if 'user' not in session:
            return redirect(url_for('auth.login'))

    # Global context: inject school settings into every template
    import sys, os as _os
    sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), 'src'))
    from database.db_manager import DatabaseManager as _DBM
    _db = _DBM()

    @app.context_processor
    def inject_school_settings():
        try:
            rows = _db.execute_query('SELECT * FROM settings WHERE id = 1')
            return {'school_settings': rows[0] if rows else {}}
        except Exception:
            return {'school_settings': {}}

    return app

"""
Flask Application Factory
"""
from flask import Flask, session, redirect, url_for, request
import os
from datetime import timedelta


from flask_cors import CORS

def create_app():
    """Create and configure the Flask application"""
    app = Flask(__name__)
    CORS(app) # Enable CORS for all routes
    
    # Configuration
    app.config['SECRET_KEY'] = 'yabatech-jss-secret-key-2025'
    app.config['DATABASE_PATH'] = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'school.db')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts 7 days
    
    # Register blueprints
    from app.routes import main, students, sessions, subjects, scores, attendance, reports, auth
    
    app.register_blueprint(auth.bp)  # Register auth first
    app.register_blueprint(main.bp)
    app.register_blueprint(students.bp)
    app.register_blueprint(sessions.bp)
    app.register_blueprint(subjects.bp)
    app.register_blueprint(scores.bp)
    app.register_blueprint(attendance.bp)
    app.register_blueprint(reports.bp)
    
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
    
    return app

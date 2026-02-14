from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
import os
from supabase import create_client, Client

bp = Blueprint('auth', __name__, url_prefix='/auth')

# Initialize Supabase client
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    return create_client(url, key)


def login_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and authentication handler"""
    if request.method == 'GET':
        # If already logged in, redirect to dashboard
        if 'user' in session:
            return redirect(url_for('main.dashboard'))
        return render_template('auth/login.html')
    
    # POST request - handle login
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400
        
        # Authenticate with Supabase
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user:
            # Store user info in session
            session['user'] = {
                'id': response.user.id,
                'email': response.user.email,
                'access_token': response.session.access_token
            }
            session.permanent = True  # Make session persistent
            
            return jsonify({
                'success': True,
                'redirect': url_for('main.dashboard')
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401
            
    except Exception as e:
        error_message = str(e)
        # Handle specific Supabase auth errors
        if 'Invalid login credentials' in error_message:
            message = 'Invalid email or password'
        elif 'Email not confirmed' in error_message:
            message = 'Please verify your email address'
        else:
            message = 'Authentication failed. Please try again.'
        
        return jsonify({
            'success': False,
            'message': message
        }), 401


@bp.route('/logout')
def logout():
    """Logout and clear session"""
    try:
        # Sign out from Supabase
        if 'user' in session and 'access_token' in session['user']:
            supabase = get_supabase()
            supabase.auth.sign_out()
    except:
        pass  # Ignore errors during logout
    
    # Clear session
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))


def get_current_user():
    """Get current logged-in user from session"""
    return session.get('user')

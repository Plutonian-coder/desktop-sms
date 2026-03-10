"""
Authentication Routes — Offline / Local SQLite implementation

Routes:
  GET/POST  /auth/login
  GET/POST  /auth/signup
  GET/POST  /auth/forgot-password
  GET/POST  /auth/reset-password
  GET       /auth/logout
"""
from flask import Blueprint, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from database.db_manager import DatabaseManager
from werkzeug.security import generate_password_hash, check_password_hash

bp = Blueprint('auth', __name__, url_prefix='/auth')
db = DatabaseManager()

DEFAULT_USERNAME = 'admin'
DEFAULT_PASSWORD = 'admin123'


def _ensure_default_user():
    """Create the default admin account if no users exist in the database."""
    try:
        rows = db.execute_query("SELECT id FROM users LIMIT 1")
        if not rows:
            db.execute_update(
                "INSERT INTO users (username, password_hash, role, security_question, security_answer_hash) VALUES (?, ?, ?, ?, ?)",
                (
                    DEFAULT_USERNAME,
                    generate_password_hash(DEFAULT_PASSWORD),
                    'admin',
                    'What is the school name?',
                    generate_password_hash('yabatech')
                )
            )
    except Exception as e:
        print(f"[Auth] Could not ensure default user: {e}")


def _add_security_columns_if_missing():
    """Safely add security_question / security_answer_hash columns to existing DBs."""
    try:
        cols = db.execute_query("PRAGMA table_info(users)")
        col_names = [c['name'] for c in cols]
        if 'security_question' not in col_names:
            db.execute_update("ALTER TABLE users ADD COLUMN security_question TEXT")
        if 'security_answer_hash' not in col_names:
            db.execute_update("ALTER TABLE users ADD COLUMN security_answer_hash TEXT")
    except Exception as e:
        print(f"[Auth] Could not add security columns: {e}")


# Run column migrations at import time (safe / idempotent)
_add_security_columns_if_missing()


def login_required(f):
    """Decorator to protect routes that require authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


# ─────────────────────────────────────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if 'user' in session:
            return redirect(url_for('main.dashboard'))
        return render_template('auth/login.html')

    try:
        if request.is_json:
            data = request.get_json()
            username = data.get('email') or data.get('username', '')
            password = data.get('password', '')
        else:
            username = request.form.get('email') or request.form.get('username', '')
            password = request.form.get('password', '')

        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'}), 400

        _ensure_default_user()

        user = db.execute_query(
            "SELECT * FROM users WHERE username = ?", (username.strip(),)
        )

        if not user or not check_password_hash(user[0]['password_hash'], password):
            return jsonify({'success': False, 'message': 'Invalid username or password'}), 401

        u = user[0]
        session['user'] = {
            'id': u['id'],
            'username': u['username'],
            'role': u.get('role', 'admin'),
        }
        session.permanent = True

        return jsonify({'success': True, 'redirect': url_for('main.dashboard')})

    except Exception as e:
        print(f"[Auth] Login error: {e}")
        return jsonify({'success': False, 'message': 'Authentication failed. Please try again.'}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  SIGN UP
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        if 'user' in session:
            return redirect(url_for('main.dashboard'))
        return render_template('auth/signup.html')

    try:
        data = request.get_json() if request.is_json else request.form

        username          = (data.get('username') or '').strip()
        password          = (data.get('password') or '').strip()
        confirm_password  = (data.get('confirm_password') or '').strip()
        security_question = (data.get('security_question') or '').strip()
        security_answer   = (data.get('security_answer') or '').strip().lower()

        # Validation
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password are required'}), 400
        if len(username) < 3:
            return jsonify({'success': False, 'message': 'Username must be at least 3 characters'}), 400
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400
        if password != confirm_password:
            return jsonify({'success': False, 'message': 'Passwords do not match'}), 400
        if not security_question or not security_answer:
            return jsonify({'success': False, 'message': 'Security question and answer are required'}), 400

        # Check uniqueness
        existing = db.execute_query("SELECT id FROM users WHERE username = ?", (username,))
        if existing:
            return jsonify({'success': False, 'message': 'That username is already taken'}), 409

        db.execute_update(
            "INSERT INTO users (username, password_hash, role, security_question, security_answer_hash) VALUES (?, ?, ?, ?, ?)",
            (
                username,
                generate_password_hash(password),
                'admin',
                security_question,
                generate_password_hash(security_answer)
            )
        )

        return jsonify({'success': True, 'message': 'Account created successfully', 'redirect': url_for('auth.login')})

    except Exception as e:
        print(f"[Auth] Signup error: {e}")
        return jsonify({'success': False, 'message': 'Could not create account. Please try again.'}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  FORGOT PASSWORD (step 1: identity + security answer)
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('auth/forgot_password.html')

    try:
        data = request.get_json() if request.is_json else request.form
        username = (data.get('username') or '').strip()

        if not username:
            return jsonify({'success': False, 'message': 'Please enter your username'}), 400

        user = db.execute_query("SELECT * FROM users WHERE username = ?", (username,))
        if not user:
            # Don't reveal whether user exists
            return jsonify({'success': False, 'message': 'No account found with that username'}), 404

        u = user[0]
        q = u.get('security_question') or None
        if not q:
            return jsonify({'success': False, 'message': 'No security question set for this account. Contact your system administrator.'}), 400

        return jsonify({'success': True, 'security_question': q})

    except Exception as e:
        print(f"[Auth] Forgot-password error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred. Please try again.'}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  RESET PASSWORD (step 2: verify answer + set new password)
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.get_json() if request.is_json else request.form

        username         = (data.get('username') or '').strip()
        security_answer  = (data.get('security_answer') or '').strip().lower()
        new_password     = (data.get('new_password') or '').strip()
        confirm_password = (data.get('confirm_password') or '').strip()

        if not all([username, security_answer, new_password, confirm_password]):
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters'}), 400

        user = db.execute_query("SELECT * FROM users WHERE username = ?", (username,))
        if not user:
            return jsonify({'success': False, 'message': 'Account not found'}), 404

        u = user[0]
        stored_hash = u.get('security_answer_hash') or ''
        if not stored_hash or not check_password_hash(stored_hash, security_answer):
            return jsonify({'success': False, 'message': 'Security answer is incorrect'}), 401

        db.execute_update(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (generate_password_hash(new_password), username)
        )

        return jsonify({'success': True, 'message': 'Password reset successfully!', 'redirect': url_for('auth.login')})

    except Exception as e:
        print(f"[Auth] Reset-password error: {e}")
        return jsonify({'success': False, 'message': 'Could not reset password. Please try again.'}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  LOGOUT
# ─────────────────────────────────────────────────────────────────────────────

@bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))


def get_current_user():
    return session.get('user')

"""Session/Term Management Routes"""
from flask import Blueprint, render_template, request, jsonify
import sys, os
import re
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from database.db_manager import DatabaseManager

bp = Blueprint('sessions', __name__, url_prefix='/sessions')
db = DatabaseManager()

def validate_session_data(data):
    """Validate session and term data"""
    errors = []

    # Session name format validation
    if not data.get('name'):
        errors.append('Session name is required')
    elif not re.match(r'^\d{4}/\d{4}$', data['name']):
        errors.append('Session name must be in format YYYY/YYYY (e.g., 2024/2025)')

    # Date validations (if start_date and end_date provided)
    if data.get('start_date') and data.get('end_date'):
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
            if end_date <= start_date:
                errors.append('Session end date must be after start date')
        except ValueError:
            errors.append('Invalid date format. Use YYYY-MM-DD')

    # Term data validation
    if not data.get('term_number'):
        errors.append('Term number is required')
    elif int(data['term_number']) not in [1, 2, 3]:
        errors.append('Term number must be 1, 2, or 3')

    if data.get('resumption_date') and data.get('vacation_date'):
        try:
            resumption = datetime.strptime(data['resumption_date'], '%Y-%m-%d')
            vacation = datetime.strptime(data['vacation_date'], '%Y-%m-%d')
            if vacation <= resumption:
                errors.append('Vacation date must be after resumption date')

            # If session dates provided, check term dates are within session
            if data.get('start_date') and data.get('end_date'):
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d')
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d')
                if resumption < start_date or resumption > end_date:
                    errors.append('Term resumption date must be within session dates')
                if vacation < start_date or vacation > end_date:
                    errors.append('Term vacation date must be within session dates')
        except ValueError:
            errors.append('Invalid date format for term dates')

    return errors

@bp.route('/')
def index():
    """Sessions/Terms management page"""
    sessions = db.execute_query('SELECT * FROM sessions ORDER BY name DESC')
    return render_template('sessions/index.html', sessions=sessions)

@bp.route('/add_academic_period', methods=['POST'])
def add_academic_period():
    """Add new session and term simultaneously with validation"""
    data = request.json

    # Validate input data
    validation_errors = validate_session_data(data)
    if validation_errors:
        return jsonify({
            'success': False,
            'message': 'Validation failed',
            'errors': validation_errors
        }), 400

    try:
        # 1. Check if session already exists
        existing_session = db.execute_query('SELECT id FROM sessions WHERE name = ?', (data['name'],))
        if existing_session:
            return jsonify({
                'success': False,
                'message': f"Session '{data['name']}' already exists"
            }), 400

        # 2. Create Session with all fields
        db.execute_update('''
            INSERT INTO sessions (name, start_date, end_date)
            VALUES (?, ?, ?)
        ''', (data['name'], data.get('start_date'), data.get('end_date')))

        # Get the newly created session
        created_session = db.execute_query('SELECT * FROM sessions WHERE name = ?', (data['name'],))
        if not created_session:
            return jsonify({
                'success': False,
                'message': 'Failed to create session'
            }), 500

        session_id = created_session[0]['id']

        # 3. Create Term
        db.execute_update('''
            INSERT INTO terms (session_id, term_number, resumption_date, vacation_date)
            VALUES (?, ?, ?, ?)
        ''', (session_id, data['term_number'],
              data.get('resumption_date'), data.get('vacation_date')))

        # Get the created term
        created_term = db.execute_query('''
            SELECT * FROM terms WHERE session_id = ? AND term_number = ?
        ''', (session_id, data['term_number']))

        return jsonify({
            'success': True,
            'message': 'Academic period created successfully',
            'session': dict(created_session[0]),
            'term': dict(created_term[0]) if created_term else None
        })

    except Exception as e:
        # Handle unique constraint specific error message
        if "UNIQUE" in str(e):
            return jsonify({
                'success': False,
                'message': f"Term {data['term_number']} already exists for this session"
            }), 400
        return jsonify({
            'success': False,
            'message': f'Failed to create academic period: {str(e)}'
        }), 500

@bp.route('/add', methods=['POST'])
def add_session():
    """Add new session (Legacy/Simple)"""
    data = request.json
    try:
        db.execute_update('INSERT INTO sessions (name) VALUES (?)', (data['name'],))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/terms/add', methods=['POST'])
def add_term():
    """Add new term to a session"""
    data = request.json
    try:
        db.execute_update('''
            INSERT INTO terms (session_id, term_number, resumption_date, vacation_date)
            VALUES (?, ?, ?, ?)
        ''', (data['session_id'], data['term_number'], 
              data.get('resumption_date'), data.get('vacation_date')))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/set_active', methods=['POST'])
def set_active():
    """Set current session and term in settings"""
    data = request.json
    print(f"[SET_ACTIVE] Received: session_id={data.get('session_id')}, term_id={data.get('term_id')}")
    try:
        result = db.execute_update('''
            UPDATE settings SET current_session_id = ?, current_term_id = ?
            WHERE id = 1
        ''', (data['session_id'], data['term_id']))
        print(f"[SET_ACTIVE] Update result: {result}")
        return jsonify({'success': True})
    except Exception as e:
        print(f"[SET_ACTIVE] ERROR: {e}")
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/details/<int:session_id>')
def get_details(session_id):
    """Get terms for a session"""
    terms = db.execute_query('SELECT * FROM terms WHERE session_id = ? ORDER BY term_number', (session_id,))
    current_settings = db.execute_query('SELECT current_session_id, current_term_id FROM settings WHERE id = 1')
    
    return jsonify({
        'terms': [dict(t) for t in terms],
        'active_session_id': current_settings[0]['current_session_id'] if current_settings else None,
        'active_term_id': current_settings[0]['current_term_id'] if current_settings else None
    })

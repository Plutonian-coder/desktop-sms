"""Fee Management Routes"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import sys, os
import uuid
import json
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from database.db_manager import DatabaseManager

bp = Blueprint('fees', __name__, url_prefix='/fees')
db = DatabaseManager()

@bp.route('/')
def index():
    """Fee management hub - view past receipts and create new ones"""
    # Fetch data needed for fee creation
    sessions = db.execute_query('SELECT * FROM sessions ORDER BY name DESC')
    current_session = db.get_current_session()
    current_term = db.get_current_term()
    classes = db.execute_query('SELECT * FROM classes ORDER BY level, stream')
    
    # Fetch recent receipts
    receipts_query = '''
        SELECT fr.*, s.first_name, s.last_name, s.reg_number 
        FROM fee_receipts fr
        JOIN students s ON fr.student_id = s.id
    '''
    recent_receipts = db.execute_query(receipts_query)
    
    return render_template('fees/index.html',
                           sessions=sessions,
                           classes=classes,
                           current_session=current_session,
                           current_term=current_term,
                           recent_receipts=recent_receipts)

@bp.route('/api/students')
def api_students():
    """Return active students as JSON"""
    students = db.execute_query('SELECT id, first_name, last_name, reg_number, class_id FROM students WHERE active_status = 1 ORDER BY last_name')
    return jsonify(students)

@bp.route('/save', methods=['POST'])
def save_receipt():
    """Save a new fee receipt"""
    data = request.json
    
    student_id = data.get('student_id')
    session_id = data.get('session_id')
    term_id = data.get('term_id')
    amount_paid = data.get('amount_paid')
    description = data.get('description', '[]')
    
    if not all([student_id, session_id, term_id, amount_paid]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
        
    try:
        # Generate a unique receipt number
        date_str = datetime.now().strftime('%Y%m')
        short_uuid = str(uuid.uuid4().hex)[:6].upper()
        receipt_number = f"RCP-{date_str}-{short_uuid}"
        
        # Save to DB
        db.execute_update('''
            INSERT INTO fee_receipts (student_id, session_id, term_id, receipt_number, amount_paid, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, session_id, term_id, receipt_number, amount_paid, description))
        
        return jsonify({'success': True, 'receipt_number': receipt_number})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/receipt/<receipt_number>')
def view_receipt(receipt_number):
    """Printable view of a saved receipt"""
    receipts = db.execute_query('''
        SELECT fr.*, s.first_name, s.last_name, s.reg_number 
        FROM fee_receipts fr
        JOIN students s ON fr.student_id = s.id
        WHERE fr.receipt_number = ?
    ''', (receipt_number,))
    
    if not receipts:
        return "Receipt not found", 404
        
    receipt = receipts[0]
    
    # Needs term info etc. We can pass it to the template
    session_info = db.execute_query('SELECT name FROM sessions WHERE id = ?', (receipt['session_id'],))
    term_info = db.execute_query('SELECT term_number FROM terms WHERE id = ?', (receipt['term_id'],))
    settings = db.execute_query('SELECT * FROM settings WHERE id = 1')
    
    try:
        items = json.loads(receipt['description'])
    except json.JSONDecodeError:
        items = []
        
    return render_template('fees/receipt.html',
                           receipt=receipt,
                           items=items,
                           session=session_info[0] if session_info else None,
                           term=term_info[0] if term_info else None,
                           settings=settings[0] if settings else None,
                           date_issued=receipt.get('payment_date', datetime.combine(datetime.now(), datetime.min.time())))

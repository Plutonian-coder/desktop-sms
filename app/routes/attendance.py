"""Attendance Routes"""
from flask import Blueprint, render_template, request, jsonify
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from database.db_manager import DatabaseManager

bp = Blueprint('attendance', __name__, url_prefix='/attendance')
db = DatabaseManager()

@bp.route('/')
def index():
    """Attendance tracking page"""
    sessions = db.execute_query('SELECT * FROM sessions ORDER BY name DESC')
    classes = db.execute_query('SELECT * FROM classes ORDER BY level, stream')
    return render_template('attendance/index.html', sessions=sessions, classes=classes)

@bp.route('/api/terms/<int:session_id>')
def get_terms(session_id):
    """Get terms for a session"""
    terms = db.execute_query('SELECT * FROM terms WHERE session_id = ? ORDER BY term_number', (session_id,))
    return jsonify([dict(t) for t in terms])

@bp.route('/api/class_attendance')
def get_class_attendance():
    """Get attendance grid for all students in a class"""
    class_id = request.args.get('class_id', type=int)
    session_id = request.args.get('session_id', type=int)
    term_id = request.args.get('term_id', type=int)
    
    if not all([class_id, session_id, term_id]):
        return jsonify([])
        
    # 1. Get all students in this class
    students = db.execute_query('''
        SELECT id, first_name, last_name, reg_number 
        FROM students 
        WHERE class_id = ? AND active_status = 1
        ORDER BY last_name, first_name
    ''', (class_id,))
    
    result = []
    for std in students:
        # 2. Get existing attendance for this student
        attendance = db.execute_query('''
            SELECT * FROM attendance 
            WHERE student_id = ? AND session_id = ? AND term_id = ?
        ''', (std['id'], session_id, term_id))
        
        att_data = attendance[0] if attendance else {}
        
        result.append({
            'student_id': std['id'],
            'full_name': f"{std['last_name']} {std['first_name']}",
            'reg_number': std['reg_number'],
            'times_present': att_data.get('times_present', 0),
            'times_absent': att_data.get('times_absent', 0)
        })
        
    return jsonify(result)

@bp.route('/api/save', methods=['POST'])
def save_attendance():
    """Save attendance for all students in a class"""
    data = request.json
    class_id = data.get('class_id')
    session_id = data.get('session_id')
    term_id = data.get('term_id')
    attendance_data = data.get('attendance', [])

    if not all([class_id, session_id, term_id]):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400

    try:
        saved_count = 0
        for entry in attendance_data:
            student_id = entry['student_id']
            times_present = int(entry['times_present'] or 0)
            times_absent = int(entry['times_absent'] or 0)

            db.execute_update('''
                INSERT OR REPLACE INTO attendance 
                (student_id, session_id, term_id, times_present, times_absent)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, session_id, term_id, times_present, times_absent))
            saved_count += 1

        return jsonify({'success': True, 'message': f'Attendance saved for {saved_count} students'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

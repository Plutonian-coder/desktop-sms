"""Student Management Routes"""
from flask import Blueprint, render_template, request, jsonify
import sys, os
import re
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from database.db_manager import DatabaseManager

bp = Blueprint('students', __name__, url_prefix='/students')
db = DatabaseManager()

def validate_student_data(data, student_id=None):
    """Validate student data before saving"""
    errors = []

    # Required fields
    required_fields = ['reg_number', 'first_name', 'last_name', 'gender', 'dob', 'class_id']
    for field in required_fields:
        if not data.get(field):
            errors.append(f"{field.replace('_', ' ').title()} is required")

    # Registration number uniqueness
    if data.get('reg_number'):
        reg_number = data['reg_number'].strip()
        if student_id:
            # Check if reg_number exists for other students
            existing = db.execute_query(
                'SELECT id FROM students WHERE reg_number = ? AND id != ? AND active_status = 1',
                (reg_number, student_id)
            )
        else:
            # Check if reg_number exists at all
            existing = db.execute_query(
                'SELECT id FROM students WHERE reg_number = ? AND active_status = 1',
                (reg_number,)
            )
        if existing:
            errors.append(f"Registration number '{reg_number}' is already in use")

    # Date format validation
    if data.get('dob'):
        try:
            datetime.strptime(data['dob'], '%Y-%m-%d')
        except ValueError:
            errors.append("Date of birth must be in YYYY-MM-DD format")

    # Phone number validation (if provided)
    if data.get('parent_phone'):
        phone = data['parent_phone'].strip()
        # Allow digits, spaces, hyphens, parentheses, and plus sign
        if not re.match(r'^[\d\s\-\(\)\+]+$', phone) or len(phone) < 10:
            errors.append("Parent phone number is invalid (minimum 10 digits)")

    # Gender validation
    if data.get('gender') and data['gender'] not in ['Male', 'Female']:
        errors.append("Gender must be either 'Male' or 'Female'")

    return errors

@bp.route('/')
def index():
    """Students list page"""
    students = db.execute_query('''
        SELECT s.*, c.name as class_name 
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.active_status = 1
        ORDER BY s.last_name, s.first_name
    ''')
    classes = db.execute_query('SELECT * FROM classes ORDER BY level, stream')
    return render_template('students/index.html', students=students, classes=classes)

@bp.route('/add', methods=['POST'])
def add_student():
    """Add new student with validation"""
    data = request.json

    # Validate input data
    validation_errors = validate_student_data(data)
    if validation_errors:
        return jsonify({
            'success': False,
            'message': 'Validation failed',
            'errors': validation_errors
        }), 400

    try:
        # Insert student
        db.execute_update('''
            INSERT INTO students (reg_number, first_name, last_name, gender, dob, class_id,
                                parent_name, parent_phone, parent_address, date_enrolled, active_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'), 1)
        ''', (data['reg_number'].strip(), data['first_name'].strip(), data['last_name'].strip(),
              data['gender'], data['dob'], data['class_id'], data.get('parent_name', '').strip(),
              data.get('parent_phone', '').strip(), data.get('parent_address', '').strip()))

        # Get the newly created student with class name
        new_student = db.execute_query('''
            SELECT s.*, c.name as class_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE s.reg_number = ? AND s.active_status = 1
        ''', (data['reg_number'].strip(),))

        if new_student:
            return jsonify({
                'success': True,
                'message': 'Student registered successfully',
                'student': dict(new_student[0])
            })
        else:
            return jsonify({'success': True, 'message': 'Student registered successfully'})

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to register student: {str(e)}'
        }), 500

@bp.route('/<int:student_id>', methods=['GET'])
def get_student(student_id):
    """Get single student details"""
    try:
        student = db.execute_query('SELECT * FROM students WHERE id = ?', (student_id,))
        if not student:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        # Convert row to dict for JSON serialization
        return jsonify(dict(student[0]))
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/update/<int:student_id>', methods=['POST'])
def update_student(student_id):
    """Update student details with validation"""
    data = request.json

    # Check if student exists
    existing = db.execute_query('SELECT id FROM students WHERE id = ? AND active_status = 1', (student_id,))
    if not existing:
        return jsonify({
            'success': False,
            'message': 'Student not found'
        }), 404

    # Validate input data
    validation_errors = validate_student_data(data, student_id)
    if validation_errors:
        return jsonify({
            'success': False,
            'message': 'Validation failed',
            'errors': validation_errors
        }), 400

    try:
        db.execute_update('''
            UPDATE students
            SET reg_number=?, first_name=?, last_name=?, gender=?, dob=?, class_id=?,
                parent_name=?, parent_phone=?, parent_address=?
            WHERE id=?
        ''', (data['reg_number'].strip(), data['first_name'].strip(), data['last_name'].strip(),
              data['gender'], data['dob'], data['class_id'], data.get('parent_name', '').strip(),
              data.get('parent_phone', '').strip(), data.get('parent_address', '').strip(), student_id))

        # Get updated student with class name
        updated_student = db.execute_query('''
            SELECT s.*, c.name as class_name
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE s.id = ?
        ''', (student_id,))

        if updated_student:
            return jsonify({
                'success': True,
                'message': 'Student updated successfully',
                'student': dict(updated_student[0])
            })
        else:
            return jsonify({'success': True, 'message': 'Student updated successfully'})

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Failed to update student: {str(e)}'
        }), 500

@bp.route('/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    """Soft delete student (set active_status = 0)"""
    try:
        db.execute_update('UPDATE students SET active_status = 0 WHERE id = ?', (student_id,))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

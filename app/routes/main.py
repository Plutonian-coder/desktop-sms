"""
Main Routes - Dashboard and Home
"""
from flask import Blueprint, render_template, jsonify
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

from database.db_manager import DatabaseManager

bp = Blueprint('main', __name__)
db = DatabaseManager()


def safe_count(result):
    """Safely extract count from query result, handling varying key names."""
    if not result:
        return 0
    row = result[0]
    return row.get('count', row.get('cnt', 0)) or 0


@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    """Dashboard with statistics"""
    # Get total active students (this query IS handled by db_manager)
    total_students_result = db.execute_query(
        'SELECT COUNT(*) as count FROM students WHERE active_status = 1'
    )
    total_students = safe_count(total_students_result)

    # Get all active students to compute gender and class stats in Python
    all_students = db.execute_query(
        'SELECT s.*, c.name as class_name FROM students s LEFT JOIN classes c ON s.class_id = c.id WHERE s.active_status = 1'
    ) or []

    # Count by gender
    male_count = sum(1 for s in all_students if str(s.get('gender', '')).upper() in ('M', 'MALE'))
    female_count = sum(1 for s in all_students if str(s.get('gender', '')).upper() in ('F', 'FEMALE'))

    # Count by class
    class_map = {}
    for s in all_students:
        cname = s.get('class_name') or 'Unassigned'
        class_map[cname] = class_map.get(cname, 0) + 1
    class_counts = [{'class_name': k, 'count': v} for k, v in sorted(class_map.items())]

    # Count subjects and classes via existing query paths
    try:
        all_subjects = db.execute_query('SELECT * FROM subjects') or []
        total_subjects = len(all_subjects)
    except Exception:
        total_subjects = 0

    try:
        all_classes = db.execute_query('SELECT * FROM classes') or []
        total_classes = len(all_classes)
    except Exception:
        total_classes = 0

    current_session = db.get_current_session()
    current_term = db.get_current_term()

    session_name = current_session['name'] if current_session else "Not Set"
    term_num = f"Term {current_term['term_number']}" if current_term else "Not Set"

    return render_template('dashboard.html',
                         total_students=total_students,
                         male_count=male_count,
                         female_count=female_count,
                         total_subjects=total_subjects,
                         total_classes=total_classes,
                         class_counts=class_counts,
                         session_name=session_name,
                         term_name=term_num)


@bp.route('/api/dashboard/analytics')
def dashboard_analytics():
    """API endpoint for dashboard chart data"""
    # Get all active students
    all_students = db.execute_query(
        'SELECT s.*, c.name as class_name FROM students s LEFT JOIN classes c ON s.class_id = c.id WHERE s.active_status = 1'
    ) or []

    # Class distribution
    class_map = {}
    for s in all_students:
        cname = s.get('class_name') or 'Unassigned'
        class_map[cname] = class_map.get(cname, 0) + 1

    # Gender distribution
    gender_map = {}
    for s in all_students:
        g = s.get('gender', 'Unknown')
        gender_map[g] = gender_map.get(g, 0) + 1

    return jsonify({
        'class_distribution': [{'label': k, 'value': v} for k, v in sorted(class_map.items())],
        'gender_distribution': [{'label': k, 'value': v} for k, v in gender_map.items()]
    })

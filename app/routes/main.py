"""
Main Routes - Dashboard and Home
"""
from flask import Blueprint, render_template
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

from database.db_manager import DatabaseManager

bp = Blueprint('main', __name__)
db = DatabaseManager()


@bp.route('/')
@bp.route('/dashboard')
def dashboard():
    """Dashboard with statistics"""
    # Get statistics
    total_students_result = db.execute_query(
        'SELECT COUNT(*) as count FROM students WHERE active_status = 1'
    )
    total_students = total_students_result[0]['count'] if total_students_result else 0
    
    current_session = db.get_current_session()
    current_term = db.get_current_term()
    
    session_name = current_session['name'] if current_session else "Not Set"
    term_num = f"Term {current_term['term_number']}" if current_term else "Not Set"
    
    return render_template('dashboard.html',
                         total_students=total_students,
                         session_name=session_name,
                         term_name=term_num)

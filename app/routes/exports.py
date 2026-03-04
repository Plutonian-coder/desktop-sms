"""
Data Export Routes - CSV export for students, scores, attendance, and fees
"""
from flask import Blueprint, Response, request
import csv
import io
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from database.db_manager import DatabaseManager

bp = Blueprint('exports', __name__, url_prefix='/exports')
db = DatabaseManager()


@bp.route('/students')
def export_students():
    """Export all active students as CSV"""
    students = db.execute_query(
        '''SELECT s.reg_number, s.first_name, s.last_name, s.gender, s.dob,
                  c.name as class_name, s.parent_name, s.parent_phone, s.parent_address
           FROM students s
           LEFT JOIN classes c ON s.class_id = c.id
           WHERE s.active_status = 1
           ORDER BY c.name, s.last_name'''
    ) or []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Reg Number', 'First Name', 'Last Name', 'Gender', 'Date of Birth',
                     'Class', 'Parent/Guardian', 'Phone', 'Address'])

    for s in students:
        writer.writerow([
            s.get('reg_number', ''),
            s.get('first_name', ''),
            s.get('last_name', ''),
            s.get('gender', ''),
            s.get('dob', ''),
            s.get('class_name', ''),
            s.get('parent_name', ''),
            s.get('parent_phone', ''),
            s.get('parent_address', '')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=students_export.csv'}
    )


@bp.route('/scores')
def export_scores():
    """Export scores for a session/term/class as CSV"""
    session_id = request.args.get('session_id')
    term_id = request.args.get('term_id')
    class_id = request.args.get('class_id')

    if not all([session_id, term_id, class_id]):
        return Response('Missing parameters: session_id, term_id, class_id required', status=400)

    # Get students in class
    students = db.execute_query(
        '''SELECT s.id, s.reg_number, s.first_name, s.last_name
           FROM students s
           WHERE s.class_id = ? AND s.active_status = 1
           ORDER BY s.last_name''',
        (class_id,)
    ) or []

    # Get subjects for the class
    subjects = db.execute_query(
        '''SELECT id, name FROM subjects WHERE class_id = ? ORDER BY name''',
        (class_id,)
    ) or []

    # Get all scores for this session/term
    scores = db.execute_query(
        '''SELECT student_id, subject_id, ca1, ca2, exam, total
           FROM scores
           WHERE session_id = ? AND term_id = ?''',
        (session_id, term_id)
    ) or []

    # Index scores by (student_id, subject_id)
    score_map = {}
    for sc in scores:
        key = (sc['student_id'], sc['subject_id'])
        score_map[key] = sc

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    header = ['Reg Number', 'Student Name']
    for subj in subjects:
        header.extend([f"{subj['name']} CA1", f"{subj['name']} CA2",
                       f"{subj['name']} Exam", f"{subj['name']} Total"])
    writer.writerow(header)

    # Data rows
    for student in students:
        row = [student['reg_number'], f"{student['last_name']} {student['first_name']}"]
        for subj in subjects:
            sc = score_map.get((student['id'], subj['id']), {})
            row.extend([
                sc.get('ca1', ''),
                sc.get('ca2', ''),
                sc.get('exam', ''),
                sc.get('total', '')
            ])
        writer.writerow(row)

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=scores_export.csv'}
    )


@bp.route('/attendance')
def export_attendance():
    """Export attendance records as CSV"""
    session_id = request.args.get('session_id')
    term_id = request.args.get('term_id')
    class_id = request.args.get('class_id')

    if not all([session_id, term_id, class_id]):
        return Response('Missing parameters: session_id, term_id, class_id required', status=400)

    records = db.execute_query(
        '''SELECT s.reg_number, s.first_name, s.last_name,
                  a.date, a.status
           FROM attendance a
           JOIN students s ON a.student_id = s.id
           WHERE a.session_id = ? AND a.term_id = ? AND s.class_id = ?
           ORDER BY a.date, s.last_name''',
        (session_id, term_id, class_id)
    ) or []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Reg Number', 'First Name', 'Last Name', 'Date', 'Status'])

    for r in records:
        writer.writerow([
            r.get('reg_number', ''),
            r.get('first_name', ''),
            r.get('last_name', ''),
            r.get('date', ''),
            r.get('status', '')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=attendance_export.csv'}
    )


@bp.route('/fees')
def export_fees():
    """Export fee records as CSV"""
    session_id = request.args.get('session_id')
    term_id = request.args.get('term_id')

    query = '''SELECT s.reg_number, s.first_name, s.last_name,
                      c.name as class_name,
                      f.amount, f.amount_paid, f.balance, f.status, f.payment_date
               FROM fees f
               JOIN students s ON f.student_id = s.id
               LEFT JOIN classes c ON s.class_id = c.id
               WHERE 1=1'''
    params = []

    if session_id:
        query += ' AND f.session_id = ?'
        params.append(session_id)
    if term_id:
        query += ' AND f.term_id = ?'
        params.append(term_id)

    query += ' ORDER BY s.last_name'

    records = db.execute_query(query, tuple(params)) or []

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Reg Number', 'First Name', 'Last Name', 'Class',
                     'Amount', 'Paid', 'Balance', 'Status', 'Payment Date'])

    for r in records:
        writer.writerow([
            r.get('reg_number', ''),
            r.get('first_name', ''),
            r.get('last_name', ''),
            r.get('class_name', ''),
            r.get('amount', ''),
            r.get('amount_paid', ''),
            r.get('balance', ''),
            r.get('status', ''),
            r.get('payment_date', '')
        ])

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=fees_export.csv'}
    )

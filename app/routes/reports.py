from flask import Blueprint, render_template, request, jsonify, send_file
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))
from database.db_manager import DatabaseManager
from logic.ranking import RankingEngine
from reports.pdf_generator import PDFGenerator

bp = Blueprint('reports', __name__, url_prefix='/reports')
db = DatabaseManager()
ranking_engine = RankingEngine()
pdf_generator = PDFGenerator()

@bp.route('/')
def index():
    """Report Generation Page"""
    sessions = db.execute_query('SELECT * FROM sessions')
    classes = db.execute_query('SELECT * FROM classes ORDER BY level, stream')
    current_session = db.get_current_session()
    current_term = db.get_current_term()
    
    return render_template('reports/index.html', 
                          sessions=sessions, 
                          classes=classes,
                          current_session=current_session,
                          current_term=current_term)

@bp.route('/calculate_ranking', methods=['POST'])
def calculate_ranking():
    """Trigger ranking calculation for a class"""
    data = request.json
    class_id = data.get('class_id')
    session_id = data.get('session_id')
    term_id = data.get('term_id')
    
    if not all([class_id, session_id, term_id]):
        return jsonify({'success': False, 'message': 'Missing parameters'})
        
    try:
        result = ranking_engine.process_class_results(class_id, session_id, term_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/generate_batch', methods=['POST'])
def generate_batch():
    """Generate reports for the whole class"""
    data = request.json
    class_id = data.get('class_id')
    session_id = data.get('session_id')
    term_id = data.get('term_id')
    
    # Output directory
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reports_output')
    
    try:
        files = pdf_generator.generate_class_reports(class_id, session_id, term_id, output_dir)
        return jsonify({'success': True, 'message': f'Generated {len(files)} reports', 'path': output_dir})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/student_report_data')
def get_student_report_data():
    """Fetch all data needed for report card editor"""
    import datetime
    student_id = request.args.get('student_id')
    class_id = request.args.get('class_id')
    session_id = request.args.get('session_id')
    term_id = request.args.get('term_id')

    if not all([student_id, session_id, term_id]):
        return jsonify({'success': False, 'message': 'Missing fields'})

    # 1. Fetch Student Info
    student = db.execute_query('SELECT * FROM students WHERE id=?', (student_id,))[0]

    # 2. Fetch Academic Scores (Formatted for Preview)
    scores = db.execute_query('''
        SELECT Sc.*, Su.name as subject_name
        FROM scores Sc
        JOIN subjects Su ON Sc.subject_id = Su.id
        WHERE Sc.student_id = ? AND Sc.session_id = ? AND Sc.term_id = ?
        ORDER BY Su.name
    ''', (student_id, session_id, term_id))

    results = []
    for s in scores:
        results.append({
            'subject': s['subject_name'],
            'ca': s['ca_score'],
            'exam': s['exam_score'],
            'total': s['total'],
            'grade': s['grade'],
            'pos': s['position'] or '-',
            'highest': s.get('class_highest') or '-',
            'lowest': s.get('class_lowest') or '-',
            'avg': s['class_average'] or '-'
        })

    # 3. Fetch Skills & Remarks
    remarks_data = db.execute_query('SELECT * FROM remarks WHERE student_id=? AND session_id=? AND term_id=?', (student_id, session_id, term_id))
    remarks = remarks_data[0] if remarks_data else {}

    affective_data = db.execute_query('SELECT * FROM affective_ratings WHERE student_id=? AND session_id=? AND term_id=?', (student_id, session_id, term_id))
    skills = {item['category']: item['rating'] for item in affective_data}

    # 4. Fetch School Settings
    settings_data = db.execute_query('SELECT * FROM settings WHERE id = 1')
    settings = settings_data[0] if settings_data else {}

    # 5. Fetch Session & Term Info
    session_info = db.execute_query('SELECT * FROM sessions WHERE id=?', (session_id,))
    session_name = session_info[0]['name'] if session_info else ''

    term_info = db.execute_query('SELECT * FROM terms WHERE id=?', (term_id,))
    term_number = term_info[0]['term_number'] if term_info else ''

    # 6. Fetch Class Info
    class_info = db.execute_query('SELECT * FROM classes WHERE id=?', (class_id,)) if class_id else []
    class_name = class_info[0]['name'] if class_info else ''

    # 7. Fetch Term Result (overall position)
    term_result_rows = db.execute_query('SELECT * FROM term_results WHERE student_id=? AND session_id=? AND term_id=?', (student_id, session_id, term_id))
    term_result = term_result_rows[0] if term_result_rows else {}

    # 8. Fetch Attendance
    attendance_data = db.execute_query('SELECT * FROM attendance WHERE student_id=? AND session_id=? AND term_id=?', (student_id, session_id, term_id))
    attendance = attendance_data[0] if attendance_data else {}

    # Count students in class for "out of" display
    student_count = 0
    if class_id:
        count_result = db.execute_query('SELECT COUNT(*) as cnt FROM students WHERE class_id=? AND active_status=1', (class_id,))
        student_count = count_result[0]['cnt'] if count_result else 0

    return jsonify({
        'success': True,
        'student': {
            'name': f"{student['last_name'].upper()} {student['first_name']}",
            'reg_number': student['reg_number'],
            'gender': student['gender'],
            'photo_url': student.get('photo_url', '')
        },
        'academic': results,
        'remarks': {
            'teacher': remarks.get('teacher_remark', ''),
            'principal': remarks.get('principal_remark', '')
        },
        'skills': skills,
        'school': {
            'name': settings.get('school_name', ''),
            'address': settings.get('address', ''),
            'website': settings.get('website', ''),
            'logo_path': settings.get('logo_path', '')
        },
        'session_name': session_name,
        'term_number': term_number,
        'class_name': class_name,
        'term_result': {
            'position': term_result.get('position', '-'),
            'total_score': term_result.get('total_score', 0),
            'average_score': term_result.get('average_score', 0),
            'class_average': term_result.get('class_average_avg', 0)
        },
        'attendance': {
            'times_present': attendance.get('times_present', '-'),
            'times_absent': attendance.get('times_absent', '-')
        },
        'student_count': student_count,
        'date': datetime.datetime.now().strftime("%d/%m/%Y")
    })

@bp.route('/api/save_report_data', methods=['POST'])
def save_report_data():
    """Save Skills and Remarks"""
    data = request.json
    student_id = data.get('student_id')
    session_id = data.get('session_id')
    term_id = data.get('term_id')
    skills = data.get('skills', {}) # dict
    remarks = data.get('remarks', {}) # dict
    
    try:
        # 1. Save Skills (Upsert)
        for category, rating in skills.items():
            # Check existing
            exist = db.execute_query('SELECT id FROM affective_ratings WHERE student_id=? AND session_id=? AND term_id=? AND category=?', 
                                    (student_id, session_id, term_id, category))
            if exist:
                db.execute_update('UPDATE affective_ratings SET rating=? WHERE id=?', (rating, exist[0]['id']))
            else:
                db.execute_update('INSERT INTO affective_ratings (student_id, session_id, term_id, category, rating) VALUES (?, ?, ?, ?, ?)',
                                  (student_id, session_id, term_id, category, rating))
                                  
        # 2. Save Remarks (Upsert)
        # Using INSERT OR REPLACE (SQLite) or Upsert logic if supported
        # We'll use a specific logic as DB manager upsert is slightly robust
        # Let's try to check existing first for safety
        exist_rem = db.execute_query('SELECT id FROM remarks WHERE student_id=? AND session_id=? AND term_id=?', (student_id, session_id, term_id))
        if exist_rem:
             db.execute_update('UPDATE remarks SET teacher_remark=?, principal_remark=? WHERE id=?', 
                               (remarks.get('teacher'), remarks.get('principal'), exist_rem[0]['id']))
        else:
            db.execute_update('INSERT INTO remarks (student_id, session_id, term_id, teacher_remark, principal_remark) VALUES (?, ?, ?, ?, ?)',
                              (student_id, session_id, term_id, remarks.get('teacher'), remarks.get('principal')))
                              
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/generate_single_report', methods=['POST'])
def generate_single_report():
    data = request.json
    student_id = data.get('student_id')
    session_id = data.get('session_id')
    term_id = data.get('term_id')
    
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reports_output')
    os.makedirs(output_dir, exist_ok=True)
    
    student = db.execute_query('SELECT reg_number FROM students WHERE id=?', (student_id,))[0]
    filename = f"Report_{student['reg_number'].replace('/', '_')}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    try:
        success = pdf_generator.generate_student_report(student_id, session_id, term_id, filepath)
        if success:
             # Return relative path for serving or opening
             # Ideally we should have a route to serve this file
             return jsonify({'success': True, 'filename': filename})
        else:
            return jsonify({'success': False, 'message': 'Failed to generate'})
    except Exception as e:
         return jsonify({'success': False, 'message': str(e)})

@bp.route('/api/upload_photo', methods=['POST'])
def upload_photo():
    """Upload student photo to Supabase Storage"""
    try:
        student_id = request.form.get('student_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'Missing student_id'}), 400
        
        if 'photo' not in request.files:
            return jsonify({'success': False, 'message': 'No photo file provided'}), 400
        
        photo = request.files['photo']
        if photo.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400
        
        # Read file content
        file_content = photo.read()
        file_ext = photo.filename.rsplit('.', 1)[1].lower() if '.' in photo.filename else 'jpg'
        
        # Upload to Supabase Storage
        file_path = f"{student_id}.{file_ext}"
        supabase = db.supabase
        
        # Upload file (will overwrite if exists)
        supabase.storage.from_('student-photos').upload(
            file_path,
            file_content,
            {'content-type': photo.content_type, 'upsert': 'true'}
        )
        
        # Get public URL
        photo_url = supabase.storage.from_('student-photos').get_public_url(file_path)
        
        # Update student record
        db.execute_update('UPDATE students SET photo_url = ? WHERE id = ?', (photo_url, student_id))
        
        return jsonify({'success': True, 'photo_url': photo_url})
    except Exception as e:
        print(f"Photo upload error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@bp.route('/download/<path:filename>')
def download_report(filename):
    """Serve the generated PDF"""
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'reports_output')
    return send_file(os.path.join(output_dir, filename), as_attachment=False)

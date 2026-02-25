import sys
import os

# Add src to python path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
from database.db_manager import DatabaseManager

db = DatabaseManager()

print("Testing Attendance Backend Logic")
try:
    # Get a class and student to test with
    classes = db.execute_query('SELECT * FROM classes LIMIT 1')
    if not classes:
        print("No classes found. Test skipped.")
        sys.exit(0)
    
    class_id = classes[0]['id']
    students = db.execute_query('SELECT * FROM students WHERE class_id = ? AND active_status = 1 LIMIT 1', (class_id,))
    if not students:
        print("No active students found in the class. Test skipped.")
        sys.exit(0)
    
    student_id = students[0]['id']
    
    # Get a session and term
    settings = db.execute_query('SELECT current_session_id, current_term_id FROM settings WHERE id = 1')[0]
    session_id = settings['current_session_id']
    term_id = settings['current_term_id']
    
    if not session_id or not term_id:
        print("No active session/term found. Test skipped.")
        sys.exit(0)
        
    print(f"Testing with Student ID: {student_id}, Session ID: {session_id}, Term ID: {term_id}")
    
    # Test Inserting/Updating Attendance
    print("Testing save attendance query...")
    times_present = 85
    times_absent = 5
    
    # Simulate the query used in our backend:
    db.execute_update('''
        INSERT OR REPLACE INTO attendance 
        (student_id, session_id, term_id, times_present, times_absent)
        VALUES (?, ?, ?, ?, ?)
    ''', (student_id, session_id, term_id, times_present, times_absent))
    
    print("Test insert succeeded.")
    
    # Test retrieving
    print("Testing retrieval query...")
    attendance = db.execute_query('''
        SELECT * FROM attendance 
        WHERE student_id = ? AND session_id = ? AND term_id = ?
    ''', (student_id, session_id, term_id))
    
    if attendance:
        att = attendance[0]
        print(f"Retrieved: Times Present: {att.get('times_present')}, Times Absent: {att.get('times_absent')}")
        if att.get('times_present') == times_present and att.get('times_absent') == times_absent:
             print("SUCCESS! Data matches.")
        else:
             print("FAILURE! Data mapped incorrectly.")
    else:
        print("FAILURE! Data not retrieved.")
        
except Exception as e:
    print(f"ERROR tracking attendance: {e}")

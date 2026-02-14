import os
import sys
from dotenv import load_dotenv
sys.path.insert(0, os.path.join(os.getcwd(), 'src'))
from database.db_manager import DatabaseManager

def test_reg():
    db = DatabaseManager()
    print("Testing Student Registration...")
    
    # Try to insert a test student
    data = (
        "TEST/REG/001", "Test", "Student", "Male", "2010-01-01", 1,
        "Parent", "08012345678", "Address"
    )
    
    try:
        query = '''
            INSERT INTO students (reg_number, first_name, last_name, gender, dob, class_id,
                                parent_name, parent_phone, parent_address, date_enrolled, active_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, date('now'), 1)
        '''
        res = db.execute_update(query, data)
        print(f"Registration Result (ID): {res}")
        
        # Verify it's there
        check = db.execute_query("SELECT id, first_name, last_name, reg_number FROM students WHERE reg_number = ?", ("TEST/REG/001",))
        print(f"Verification Check: {check}")
        
        # Cleanup
        if res:
             db.supabase.table('students').delete().eq('id', res).execute()
             print("Cleanup successful")
             
    except Exception as e:
        print(f"Error during registration: {e}")

if __name__ == "__main__":
    test_reg()

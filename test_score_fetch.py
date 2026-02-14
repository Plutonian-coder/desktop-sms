from src.database.db_manager import DatabaseManager

db = DatabaseManager()

# Mock query from scores.py
query = '''
        SELECT id, first_name, last_name, reg_number
        FROM students 
        WHERE class_id = ? AND active_status = 1
        ORDER BY last_name, first_name
    '''
    
normalized = " ".join(query.lower().split())
print(f"Normalized: {normalized}")

# Try with a likely class ID (e.g., 1)
try:
    print("Executing query...")
    res = db.execute_query(query, (1,))
    print(f"Result (Class 1): {res}")
    
    # Try getting all students to see their class_ids
    all_std = db.execute_query("SELECT s.*, c.name as class_name FROM students s LEFT JOIN classes c ON s.class_id = c.id WHERE s.active_status = 1")
    print("\nAll Students & Class IDs:")
    for s in all_std:
        print(f"ID: {s['id']}, Name: {s['first_name']} {s['last_name']}, ClassID: {s['class_id']}")
        
except Exception as e:
    print(f"Error: {e}")

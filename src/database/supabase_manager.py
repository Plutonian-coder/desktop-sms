import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

class SupabaseManager:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in .env")
        self.supabase: Client = create_client(url, key)

    # Student Management
    def get_students(self, class_id=None):
        query = self.supabase.table('students').select('*, classes(name)').eq('active_status', 1)
        if class_id:
            query = query.eq('class_id', class_id)
        return query.order('last_name').execute().data

    def add_student(self, data):
        return self.supabase.table('students').insert(data).execute().data

    def update_student(self, student_id, data):
        return self.supabase.table('students').update(data).eq('id', student_id).execute().data

    def delete_student(self, student_id):
        return self.supabase.table('students').update({'active_status': 0}).eq('id', student_id).execute().data

    # Session / Term
    def get_sessions(self):
        return self.supabase.table('sessions').select('*').order('name', desc=True).execute().data

    def add_session(self, name):
        return self.supabase.table('sessions').insert({'name': name}).execute().data

    def get_terms(self, session_id):
        return self.supabase.table('terms').select('*').eq('session_id', session_id).order('term_number').execute().data

    # Subjects
    def get_all_subjects(self):
        return self.supabase.table('subjects').select('*').order('name').execute().data

    def get_class_subjects(self, class_id):
        return self.supabase.table('class_subjects').select('subject_id, subjects(*)').eq('class_id', class_id).execute().data

    # Scores
    def get_scores(self, student_id, session_id, term_id, subject_id=None):
        query = self.supabase.table('scores').select('*').eq('student_id', student_id).eq('session_id', session_id).eq('term_id', term_id)
        if subject_id:
            query = query.eq('subject_id', subject_id)
        return query.execute().data

    def save_score(self, score_data):
        # Insert or Update (upsert)
        return self.supabase.table('scores').upsert(score_data).execute().data

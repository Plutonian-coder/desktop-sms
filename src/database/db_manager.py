import os
from supabase import create_client, Client, ClientOptions
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

load_dotenv()

class DatabaseManager:
    """
    Supabase Implementation of DatabaseManager.
    Translates SQLite queries used in the app to Supabase SDK calls.
    """
    _client: Optional[Client] = None

    @property
    def supabase(self) -> Client:
        if DatabaseManager._client is None:
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")
            if not url or not key:
                # Log or raise error instead of empty strings
                raise ValueError("SUPABASE_URL or SUPABASE_KEY missing in environment")
            
            # Increase timeout for more stable connections on Windows
            from httpx import Timeout
            DatabaseManager._client = create_client(
                url, 
                key,
                options=ClientOptions(
                    postgrest_client_timeout=Timeout(20.0, connect=10.0)
                )
            )
        return DatabaseManager._client

    def __init__(self):
        # We use the property for access
        pass

    def initialize_database(self):
        # Tables should be created via supabase_setup.sql in the dashboard
        pass

    def _safe_int(self, val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return val

    def _normalize_sql(self, query: str) -> str:
        """Normalize SQL for pattern matching: lowercase, collapse whitespace, space around = and ,"""
        import re
        q = " ".join(query.lower().split())
        # Ensure spaces around '=' for consistent pattern matching (but not ==, !=, <=, >=)
        q = re.sub(r'(?<![!<>])=(?!=)', ' = ', q)
        q = " ".join(q.split())  # re-collapse any double spaces
        return q

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        q = self._normalize_sql(query)
        # Safe cast params to int if they look like digits (for Supabase .eq() stability)
        params = tuple(self._safe_int(p) for p in params)
        
        # --- Sessions ---
        if "select * from sessions" in q:
            if "where id" in q:
                return self.supabase.table('sessions').select('*').eq('id', params[0]).execute().data
            return self.supabase.table('sessions').select('*').order('name', desc=True).execute().data
        
        # --- Classes ---
        if "select * from classes" in q:
            if "where id = ?" in q:
                return self.supabase.table('classes').select('*').eq('id', params[0]).execute().data
            return self.supabase.table('classes').select('*').order('level').order('stream').execute().data
            
        # --- Students ---
        if "select s.*, c.name as class_name from students s" in q:
            # Handle filtered selection (single student after registration or update)
            query_parts = q.split('where')
            res = self.supabase.table('students').select('*, classes(name)').eq('active_status', 1)
            
            if len(query_parts) > 1:
                where_clause = query_parts[1]
                if "s.reg_number = ?" in where_clause:
                    res = res.eq('reg_number', params[0])
                elif "s.id = ?" in where_clause:
                    res = res.eq('id', params[0])
            
            res = res.order('last_name').execute()
            data = res.data
            for item in data:
                item['class_name'] = item.get('classes', {}).get('name') if item.get('classes') else None
            return data

        if "select count(*) as count from students" in q or "select count(*) as cnt from students" in q:
            if "class_id" in q:
                res = self.supabase.table('students').select('*', count='exact').eq('class_id', params[0]).eq('active_status', 1).execute()
            else:
                res = self.supabase.table('students').select('*', count='exact').eq('active_status', 1).execute()
            return [{'count': res.count, 'cnt': res.count}]

        if "from students where id = ?" in q and "count" not in q:
            return self.supabase.table('students').select('*').eq('id', params[0]).execute().data

        if "select id, first_name, last_name, reg_number from students" in q:
            return self.supabase.table('students').select('id, first_name, last_name, reg_number').eq('class_id', params[0]).eq('active_status', 1).order('last_name').execute().data

        # --- Subjects & Class Assignments ---
        if "from subjects" in q:
            if "join class_subjects" in q:
                # Handle both select s.* and select s.id, s.name, s.code
                select_fields = 'subject_id, subjects(*)' if "s.*" in q else 'subject_id, subjects(id, name, code)'
                res = self.supabase.table('class_subjects').select(select_fields).eq('class_id', params[0]).execute()
                return [item['subjects'] for item in res.data if item.get('subjects')]
            
            if "where id = ?" in q:
                return self.supabase.table('subjects').select('*').eq('id', params[0]).execute().data
            return self.supabase.table('subjects').select('*').order('name').execute().data

        if "from class_subjects" in q:
            if "count(*) as count" in q:
                res = self.supabase.table('class_subjects').select('*', count='exact').eq('class_id', params[0]).execute()
                return [{'count': res.count}]
            if "select subject_id" in q:
                return self.supabase.table('class_subjects').select('subject_id').eq('class_id', params[0]).execute().data
            if "select class_id" in q:
                return self.supabase.table('class_subjects').select('class_id').eq('subject_id', params[0]).execute().data
            return self.supabase.table('class_subjects').select('*').execute().data

        # --- Terms ---
        if "select * from terms where session_id = ?" in q:
            return self.supabase.table('terms').select('*').eq('session_id', params[0]).order('term_number').execute().data

        # --- Sessions / Terms ---
        if "from sessions" in q:
            if "where name = ?" in q:
                return self.supabase.table('sessions').select('*').eq('name', params[0]).execute().data
            if "where id = ?" in q:
                return self.supabase.table('sessions').select('*').eq('id', params[0]).execute().data
            return self.supabase.table('sessions').select('*').order('name', desc=True).execute().data

        if "from terms" in q:
            if "where id = ?" in q:
                return self.supabase.table('terms').select('*').eq('id', params[0]).execute().data
            if "session_id = ? and term_number = ?" in q:
                return self.supabase.table('terms').select('*').eq('session_id', params[0]).eq('term_number', params[1]).execute().data
            if "session_id = ?" in q:
                return self.supabase.table('terms').select('*').eq('session_id', params[0]).order('term_number').execute().data
            return self.supabase.table('terms').select('*').execute().data

        # --- Settings ---
        if "from settings" in q:
            return self.supabase.table('settings').select('*, current_session_id, current_term_id').eq('id', 1).execute().data

        # --- Scores & Ranking (Used by RankingEngine) ---
        if "from scores" in q:
            # Scores JOIN subjects (for report card academic data)
            if "join subjects" in q and "sc.student_id" in q:
                res = self.supabase.table('scores').select('*, subjects(name)') \
                    .eq('student_id', params[0]) \
                    .eq('session_id', params[1]) \
                    .eq('term_id', params[2]) \
                    .execute()
                data = res.data
                for item in data:
                    item['subject_name'] = item.get('subjects', {}).get('name', '') if item.get('subjects') else ''
                data.sort(key=lambda x: x.get('subject_name', ''))
                return data

            if "where student_id = ? and subject_id = ? and session_id = ? and term_id = ?" in q:
                return self.supabase.table('scores').select('*').eq('student_id', params[0]).eq('subject_id', params[1]).eq('session_id', params[2]).eq('term_id', params[3]).execute().data

            # Scores for a single student (all subjects) - without JOIN
            if ("where student_id = ? and session_id = ? and term_id = ?" in q or
                "where sc.student_id = ? and sc.session_id = ? and sc.term_id = ?" in q):
                return self.supabase.table('scores').select('*').eq('student_id', params[0]).eq('session_id', params[1]).eq('term_id', params[2]).execute().data

            if "total from scores s" in q:
                # JOIN scores + students handled via !inner
                res = self.supabase.table('scores').select('id, student_id, subject_id, total, students!inner(class_id, active_status)') \
                    .eq('students.class_id', params[0]) \
                    .eq('session_id', params[1]) \
                    .eq('term_id', params[2]) \
                    .eq('students.active_status', 1).execute()
                return res.data

        # --- Term Results ---
        if "from term_results" in q:
            return self.supabase.table('term_results').select('*').eq('student_id', params[0]).eq('session_id', params[1]).eq('term_id', params[2]).execute().data

        # --- Remarks ---
        if "from remarks" in q:
            if "select id from remarks" in q:
                return self.supabase.table('remarks').select('id').eq('student_id', params[0]).eq('session_id', params[1]).eq('term_id', params[2]).execute().data
            return self.supabase.table('remarks').select('*').eq('student_id', params[0]).eq('session_id', params[1]).eq('term_id', params[2]).execute().data

        # --- Affective Ratings ---
        if "from affective_ratings" in q:
            if "select id from affective_ratings" in q and "category" in q:
                return self.supabase.table('affective_ratings').select('id').eq('student_id', params[0]).eq('session_id', params[1]).eq('term_id', params[2]).eq('category', params[3]).execute().data
            return self.supabase.table('affective_ratings').select('*').eq('student_id', params[0]).eq('session_id', params[1]).eq('term_id', params[2]).execute().data

        # --- Attendance ---
        if "select * from attendance" in q:
            return self.supabase.table('attendance').select('*').eq('student_id', params[0]).eq('session_id', params[1]).eq('term_id', params[2]).execute().data

        print(f"Warning: execute_query received untranslated SQL: {query}")
        return []

    def execute_update(self, query: str, params: tuple = ()) -> int:
        q = self._normalize_sql(query)
        params = tuple(self._safe_int(p) for p in params)

        # --- Students ---
        if "insert into students" in q:
            data = {
                'reg_number': params[0], 'first_name': params[1], 'last_name': params[2],
                'gender': params[3], 'dob': params[4], 'class_id': params[5],
                'parent_name': params[6], 'parent_phone': params[7], 'parent_address': params[8]
            }
            res = self.supabase.table('students').insert(data).execute()
            return res.data[0]['id'] if res.data else 0

        if "update students set" in q:
            data = {
                'reg_number': params[0], 'first_name': params[1], 'last_name': params[2],
                'gender': params[3], 'dob': params[4], 'class_id': params[5],
                'parent_name': params[6], 'parent_phone': params[7], 'parent_address': params[8]
            }
            # Detect ID param (last one usually)
            self.supabase.table('students').update(data).eq('id', params[9]).execute()
            return params[9]

        if "update students set active_status = 0" in q:
            self.supabase.table('students').update({'active_status': 0}).eq('id', params[0]).execute()
            return params[0]

        if "update students set photo_url" in q:
            # UPDATE students SET photo_url = ? WHERE id = ?
            self.supabase.table('students').update({'photo_url': params[0]}).eq('id', params[1]).execute()
            return params[1]

        # --- Sessions / Terms ---
        # --- Sessions / Terms ---
        if "insert into sessions" in q:
            # Handle both simple (name only) and full (date) inserts implies checking params length or query structure
            if "start_date" in q:
                # INSERT INTO sessions (name, start_date, end_date) ...
                data = {'name': params[0], 'start_date': params[1], 'end_date': params[2]}
                res = self.supabase.table('sessions').insert(data).execute()
                return res.data[0]['id'] if res.data else 0
            elif "insert or ignore" not in q:
                 # Legacy simple insert (if any)
                 res = self.supabase.table('sessions').insert({'name': params[0]}).execute()
                 return res.data[0]['id'] if res.data else 0

        if "insert or ignore into sessions" in q:
            res = self.supabase.table('sessions').upsert({'name': params[0]}, on_conflict='name').execute()
            return res.data[0]['id'] if res.data else 0

        if "insert into terms" in q:
            data = {'session_id': params[0], 'term_number': params[1], 'resumption_date': params[2], 'vacation_date': params[3]}
            res = self.supabase.table('terms').insert(data).execute()
            return res.data[0]['id'] if res.data else 0

        # --- Scores ---
        if "insert or replace into scores" in q:
            data = {
                'student_id': params[0], 'subject_id': params[1], 'session_id': params[2], 'term_id': params[3],
                'ca_score': params[4], 'exam_score': params[5], 'total': params[6], 'grade': params[7]
            }
            res = self.supabase.table('scores').upsert(data, on_conflict='student_id,subject_id,session_id,term_id').execute()
            return 1

        # --- Subjects & Class Assignments ---
        if "insert into subjects" in q:
            data = {'name': params[0], 'code': params[1]}
            res = self.supabase.table('subjects').insert(data).execute()
            return res.data[0]['id'] if res.data else 0

        if "insert into class_subjects" in q:
            data = {'class_id': params[0], 'subject_id': params[1]}
            res = self.supabase.table('class_subjects').insert(data).execute()
            return res.data[0]['id'] if res.data else 0

        if "delete from class_subjects" in q:
            query_parts = q.split('where')[1]
            if "class_id = ? and subject_id = ?" in query_parts:
                self.supabase.table('class_subjects').delete().eq('class_id', params[0]).eq('subject_id', params[1]).execute()
            elif "class_id = ?" in query_parts:
                 self.supabase.table('class_subjects').delete().eq('class_id', params[0]).execute()
            return 1

        if "update subjects set code" in q:
            self.supabase.table('subjects').update({'code': params[0]}).eq('id', params[1]).execute()
            return params[1]

        # --- Affective Ratings ---
        if "update affective_ratings set rating" in q:
            self.supabase.table('affective_ratings').update({'rating': params[0]}).eq('id', params[1]).execute()
            return 1

        if "insert into affective_ratings" in q:
            data = {
                'student_id': params[0], 'session_id': params[1], 'term_id': params[2],
                'category': params[3], 'rating': params[4]
            }
            self.supabase.table('affective_ratings').insert(data).execute()
            return 1

        # --- Remarks ---
        if "update remarks set" in q:
            self.supabase.table('remarks').update({
                'teacher_remark': params[0], 'principal_remark': params[1]
            }).eq('id', params[2]).execute()
            return 1

        if "insert into remarks" in q:
            data = {
                'student_id': params[0], 'session_id': params[1], 'term_id': params[2],
                'teacher_remark': params[3], 'principal_remark': params[4]
            }
            self.supabase.table('remarks').insert(data).execute()
            return 1

        # --- Ranking (RankingEngine deletes/inserts) ---
        if "delete from term_results" in q:
            self.supabase.table('term_results').delete().eq('session_id', params[0]).eq('term_id', params[1]).eq('class_id', params[2]).execute()
            return 1

        # --- Settings (Current Session/Term) ---
        if "update settings set current_session_id" in q:
            # UPDATE settings SET current_session_id = ?, current_term_id = ? WHERE id = 1
            data = {'current_session_id': params[0], 'current_term_id': params[1]}
            self.supabase.table('settings').update(data).eq('id', 1).execute()
            return 1

        # --- Attendance ---
        if "insert into attendance" in q or "insert or replace into attendance" in q:
            data = {
                'student_id': params[0], 'session_id': params[1], 'term_id': params[2],
                'days_present': params[3], 'days_absent': params[4]
            }
            self.supabase.table('attendance').upsert(data, on_conflict='student_id,session_id,term_id').execute()
            return 1

        print(f"Warning: execute_update received untranslated SQL: {query}")
        return 0

    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        q = query.lower().strip()
        # Normalize each tuple in the list
        params_list = [tuple(self._safe_int(p) for p in params) for params in params_list]
        
        if "update scores" in q and "set position" in q:
            # We iterate because different rows have different values to update.
            # Supabase upsert requires all values, but here we update specific columns.
            # Efficient way: No obvious batch update for different values in Supabase SDK yet, so loop is fine for class size (~50).
            for p in params_list:
                data = {'position': p[0], 'class_highest': p[1], 'class_lowest': p[2], 'class_average': p[3]}
                self.supabase.table('scores').update(data).eq('id', p[4]).execute()
        
        elif "insert into term_results" in q:
            batch = []
            for p in params_list:
                batch.append({
                    'student_id': p[0], 'session_id': p[1], 'term_id': p[2], 'class_id': p[3],
                    'total_score': p[4], 'average_score': p[5], 'position': p[6],
                    'class_highest_avg': p[7], 'class_lowest_avg': p[8], 'class_average_avg': p[9]
                })
            self.supabase.table('term_results').insert(batch).execute()

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        settings = self.execute_query('SELECT current_session_id FROM settings WHERE id = 1')
        if settings and settings[0].get('current_session_id'):
            session_id = settings[0]['current_session_id']
            res = self.supabase.table('sessions').select('*').eq('id', session_id).execute()
            return res.data[0] if res.data else None
        return None

    def get_current_term(self) -> Optional[Dict[str, Any]]:
        settings = self.execute_query('SELECT current_term_id FROM settings WHERE id = 1')
        if settings and settings[0].get('current_term_id'):
            term_id = settings[0]['current_term_id']
            res = self.supabase.table('terms').select('*').eq('id', term_id).execute()
            return res.data[0] if res.data else None
        return None

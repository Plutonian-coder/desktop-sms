import pandas as pd
from database.db_manager import DatabaseManager

class RankingEngine:
    """
    Handles all ranking and statistical calculations for academic results.
    Uses Pandas for efficient in-memory processing.
    """
    
    def __init__(self):
        self.db = DatabaseManager()

    def process_class_results(self, class_id: int, session_id: int, term_id: int):
        """
        Main entry point: Calculates all rankings for a specific class/session/term.
        1. Calculates subject-based stats (Position, Average, High, Low)
        2. Calculates overall term stats (Total, Average, position)
        3. Updates the database
        """
        # 1. Fetch all raw scores for this class context
        # We need student_id, subject_id, total, ca, exam
        query = '''
            SELECT s.id, s.student_id, s.subject_id, s.total
            FROM scores s
            JOIN students st ON s.student_id = st.id
            WHERE st.class_id = ? AND s.session_id = ? AND s.term_id = ? AND st.active_status = 1
        '''
        rows = self.db.execute_query(query, (class_id, session_id, term_id))
        
        if not rows:
            return {'success': False, 'message': 'No scores found for this class'}

        # Convert to DataFrame
        df = pd.DataFrame([dict(row) for row in rows])
        
        if df.empty:
            return {'success': False, 'message': 'No data to process'}

        # --- PART A: SUBJECT RANKING ---
        # Group by subject to calculate positions and stats
        
        # Calculate Position per subject (Descending order of Total)
        # dense: 1, 2, 2, 3 (no gaps) or min: 1, 2, 2, 4 (gaps). 'min' is standard in schools.
        df['subject_position'] = df.groupby('subject_id')['total'].rank(method='min', ascending=False)
        
        # Calculate Subject Stats (stored in a separate DF to merge or just iterate)
        subject_stats = df.groupby('subject_id')['total'].agg(['mean', 'max', 'min']).reset_index()
        subject_stats.columns = ['subject_id', 'class_average', 'class_highest', 'class_lowest']
        
        # Merge stats back to main DF so each row knows its subject's stats
        df = df.merge(subject_stats, on='subject_id')
        
        # Update 'scores' table with these values
        # We do this efficiently by iterating or using executemany? 
        # For simplicity/safety, we can iterate for now, or batch update.
        update_params = []
        for _, row in df.iterrows():
            update_params.append((
                row['subject_position'],
                row['class_highest'],
                row['class_lowest'],
                round(row['class_average'], 2),
                row['id'] # scores.id
            ))
            
        self.db.execute_many('''
            UPDATE scores 
            SET position = ?, class_highest = ?, class_lowest = ?, class_average = ?
            WHERE id = ?
        ''', update_params)
        
        
        # --- PART B: OVERALL TERM RANKING ---
        # Pivot or Group by Student to get Grand Total
        student_summary = df.groupby('student_id')['total'].agg(['sum', 'mean']).reset_index()
        student_summary.columns = ['student_id', 'grand_total', 'overall_average']
        
        # Calculate Overall Position
        student_summary['overall_position'] = student_summary['overall_average'].rank(method='min', ascending=False)
        
        # Calculate Class Stats for the summary (Avg of Averages)
        class_avg_avg = student_summary['overall_average'].mean()
        class_highest_avg = student_summary['overall_average'].max()
        class_lowest_avg = student_summary['overall_average'].min()
        
        # Upate 'term_results' table
        # First, ensure records exist or replace them
        term_result_params = []
        for _, row in student_summary.iterrows():
            term_result_params.append((
                row['student_id'],
                session_id,
                term_id,
                class_id,
                row['grand_total'],
                round(row['overall_average'], 2),
                row['overall_position'],
                round(class_highest_avg, 2),
                round(class_lowest_avg, 2),
                round(class_avg_avg, 2)
            ))
            
        # We use INSERT OR REPLACE equivalent logic. 
        # Since we have a UNIQUE constraint (student, session, term), we can use REPLACE INTO or UPSERT.
        # SQLite 'REPLACE INTO' deletes and re-inserts, losing ID if referenced elsewhere? 
        # Better to try update, if fail then insert? Or simpler: Delete all for this context and re-insert?
        # Re-insertion is safest for "re-calculation".
        
        # 1. Clear old term results for this class context (to avoid duplicates/stale data)
        # Note: We need to be careful not to delete data for OTHER classes.
        # But wait, term_results has student_id.
        
        self.db.execute_update('''
            DELETE FROM term_results 
            WHERE session_id = ? AND term_id = ? AND class_id = ?
        ''', (session_id, term_id, class_id))
        
        self.db.execute_many('''
            INSERT INTO term_results (
                student_id, session_id, term_id, class_id, 
                total_score, average_score, position, 
                class_highest_avg, class_lowest_avg, class_average_avg
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', term_result_params)

        return {'success': True, 'message': 'Ranking calculation complete'}

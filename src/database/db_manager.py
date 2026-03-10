"""
DatabaseManager — Pure SQLite Implementation
Replaces the previous Supabase adapter.
All routes pass raw SQL with ? placeholders; this class executes them directly.
"""
import os
import sys
import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path


def _get_db_path() -> str:
    """
    Resolve the path to school.db.
    - In a PyInstaller frozen app: next to the .exe (cwd is set to exe dir in run.py).
    - In development: <project_root>/data/school.db
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller sets sys._MEIPASS; the exe's cwd is set in run.py
        base = os.path.dirname(sys.executable)
    else:
        # Development: two levels up from this file (src/database/ -> project root)
        base = str(Path(__file__).parent.parent.parent)

    data_dir = os.path.join(base, 'data')
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'school.db')


DB_PATH = _get_db_path()


def _get_connection() -> sqlite3.Connection:
    """Return a WAL-mode connection with row_factory set to sqlite3.Row."""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    # WAL mode: allows concurrent reads while a write is happening
    conn.execute("PRAGMA journal_mode=WAL")
    # Enforce foreign-key constraints
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


class DatabaseManager:
    """
    Thin wrapper around sqlite3.
    Public API is identical to the previous Supabase adapter so that
    all callers (routes, ranking engine, etc.) work without modification.
    """

    def initialize_database(self):
        """
        Create all tables if they don't already exist.
        Reads sqlite_setup.sql from the project root.
        """
        if getattr(sys, 'frozen', False):
            sql_path = os.path.join(os.path.dirname(sys.executable), 'sqlite_setup.sql')
        else:
            sql_path = str(Path(__file__).parent.parent.parent / 'sqlite_setup.sql')

        if not os.path.exists(sql_path):
            # Fallback: run the embedded DDL so packaging still works even if
            # the .sql file wasn't bundled.
            self._run_embedded_ddl()
            return

        with open(sql_path, 'r', encoding='utf-8') as f:
            ddl = f.read()

        with _get_connection() as conn:
            conn.executescript(ddl)

    def _run_embedded_ddl(self):
        """Emergency fallback DDL in case sqlite_setup.sql is missing."""
        from database.db_schema import SCHEMA_SQL
        with _get_connection() as conn:
            conn.executescript(SCHEMA_SQL)

    # ------------------------------------------------------------------ #
    #  Core query methods                                                  #
    # ------------------------------------------------------------------ #

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """SELECT → list of dicts."""
        try:
            with _get_connection() as conn:
                cur = conn.execute(query, params)
                rows = cur.fetchall()
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            print(f"[DB] execute_query error: {e}\nQuery: {query}\nParams: {params}")
            return []

    def execute_update(self, query: str, params: tuple = ()) -> int:
        """INSERT / UPDATE / DELETE → lastrowid (for INSERTs) or rowcount."""
        try:
            with _get_connection() as conn:
                cur = conn.execute(query, params)
                conn.commit()
                # lastrowid is set on INSERT; for UPDATE/DELETE return rowcount
                return cur.lastrowid if cur.lastrowid else cur.rowcount
        except sqlite3.IntegrityError as e:
            print(f"[DB] IntegrityError: {e}\nQuery: {query}\nParams: {params}")
            raise
        except sqlite3.Error as e:
            print(f"[DB] execute_update error: {e}\nQuery: {query}\nParams: {params}")
            raise

    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Batch INSERT / UPDATE."""
        if not params_list:
            return
        try:
            with _get_connection() as conn:
                conn.executemany(query, params_list)
                conn.commit()
        except sqlite3.Error as e:
            print(f"[DB] execute_many error: {e}\nQuery: {query}")
            raise

    # ------------------------------------------------------------------ #
    #  Convenience helpers (called by route files)                         #
    # ------------------------------------------------------------------ #

    def count_students_by_prefix(self, prefix: str) -> int:
        """Count active students whose reg_number starts with the given prefix."""
        rows = self.execute_query(
            "SELECT COUNT(*) AS cnt FROM students WHERE reg_number LIKE ? AND active_status = 1",
            (f"{prefix}%",)
        )
        return rows[0]['cnt'] if rows else 0

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        rows = self.execute_query("SELECT current_session_id FROM settings WHERE id = 1")
        if rows and rows[0].get('current_session_id'):
            sess = self.execute_query(
                "SELECT * FROM sessions WHERE id = ?",
                (rows[0]['current_session_id'],)
            )
            return sess[0] if sess else None
        return None

    def get_current_term(self) -> Optional[Dict[str, Any]]:
        rows = self.execute_query("SELECT current_term_id FROM settings WHERE id = 1")
        if rows and rows[0].get('current_term_id'):
            term = self.execute_query(
                "SELECT * FROM terms WHERE id = ?",
                (rows[0]['current_term_id'],)
            )
            return term[0] if term else None
        return None

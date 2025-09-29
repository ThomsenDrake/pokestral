import sqlite3
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str = 'pokemon_blue.db'):
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Initialize the database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create runs table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    performance_metrics TEXT
                )
            ''')

            # Create events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    details TEXT,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                )
            ''')

            # Create summaries table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    summary_text TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                )
            ''')

            # Create errors table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    error_type TEXT NOT NULL,
                    error_message TEXT NOT NULL,
                    traceback TEXT,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                )
            ''')

            conn.commit()

    def create_run(self, start_time: str, status: str, performance_metrics: str = '') -> int:
        """Create a new run record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO runs (start_time, status, performance_metrics) VALUES (?, ?, ?)',
                (start_time, status, performance_metrics)
            )
            conn.commit()
            return cursor.lastrowid

    def update_run(self, run_id: int, end_time: Optional[str] = None, status: Optional[str] = None,
                  performance_metrics: Optional[str] = None):
        """Update an existing run record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            updates = []
            params = []

            if end_time is not None:
                updates.append('end_time = ?')
                params.append(end_time)
            if status is not None:
                updates.append('status = ?')
                params.append(status)
            if performance_metrics is not None:
                updates.append('performance_metrics = ?')
                params.append(performance_metrics)

            params.append(run_id)
            cursor.execute(
                f'UPDATE runs SET {", ".join(updates)} WHERE id = ?',
                params
            )
            conn.commit()

    def get_run(self, run_id: int) -> Optional[Dict[str, Any]]:
        """Get a run record by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM runs WHERE id = ?', (run_id,))
            row = cursor.fetchone()
            return dict(zip([column[0] for column in cursor.description], row)) if row else None

    def get_all_runs(self) -> List[Dict[str, Any]]:
        """Get all run records."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM runs')
            rows = cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

    def create_event(self, run_id: int, timestamp: str, event_type: str, details: str = '') -> int:
        """Create a new event record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO events (run_id, timestamp, event_type, details) VALUES (?, ?, ?, ?)',
                (run_id, timestamp, event_type, details)
            )
            conn.commit()
            return cursor.lastrowid

    def get_events_for_run(self, run_id: int) -> List[Dict[str, Any]]:
        """Get all events for a specific run."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM events WHERE run_id = ?', (run_id,))
            rows = cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

    def create_summary(self, run_id: int, timestamp: str, summary_text: str) -> int:
        """Create a new summary record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO summaries (run_id, timestamp, summary_text) VALUES (?, ?, ?)',
                (run_id, timestamp, summary_text)
            )
            conn.commit()
            return cursor.lastrowid

    def get_summaries_for_run(self, run_id: int) -> List[Dict[str, Any]]:
        """Get all summaries for a specific run."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM summaries WHERE run_id = ?', (run_id,))
            rows = cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

    def create_error(self, run_id: int, timestamp: str, error_type: str, error_message: str,
                    traceback: str = '') -> int:
        """Create a new error record."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO errors (run_id, timestamp, error_type, error_message, traceback) VALUES (?, ?, ?, ?, ?)',
                (run_id, timestamp, error_type, error_message, traceback)
            )
            conn.commit()
            return cursor.lastrowid

    def get_errors_for_run(self, run_id: int) -> List[Dict[str, Any]]:
        """Get all errors for a specific run."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM errors WHERE run_id = ?', (run_id,))
            rows = cursor.fetchall()
            return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
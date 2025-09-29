import logging
import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any
import psutil
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('pokemon_blue_agent')

class AgentLogger:
    def __init__(self, db_path: str = 'database/pokemon_blue.db'):
        self.db_path = db_path
        self._initialize_database()

    def _initialize_database(self):
        """Ensure the database is initialized."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Create runs table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT NOT NULL,
                    end_time TEXT,
                    status TEXT NOT NULL,
                    performance_metrics TEXT
                )
            ''')

            # Create events table if not exists
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

            # Create summaries table if not exists
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS summaries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id INTEGER NOT NULL,
                    timestamp TEXT NOT NULL,
                    summary_text TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(id)
                )
            ''')

            # Create errors table if not exists
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

    def start_run(self) -> int:
        """Start a new run and return the run ID."""
        start_time = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO runs (start_time, status) VALUES (?, ?)',
                (start_time, 'running')
            )
            conn.commit()
            run_id = cursor.lastrowid
            logger.info(f"Started new run with ID {run_id}")
            return run_id

    def end_run(self, run_id: int, status: str = 'completed', performance_metrics: str = ''):
        """End a run with the given status and performance metrics."""
        end_time = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE runs SET end_time = ?, status = ?, performance_metrics = ? WHERE id = ?',
                (end_time, status, performance_metrics, run_id)
            )
            conn.commit()
            logger.info(f"Ended run {run_id} with status {status}")

    def log_event(self, run_id: int, event_type: str, details: str = ''):
        """Log an event for a specific run."""
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO events (run_id, timestamp, event_type, details) VALUES (?, ?, ?, ?)',
                (run_id, timestamp, event_type, details)
            )
            conn.commit()
            logger.info(f"Logged event {event_type} for run {run_id}")

    def log_summary(self, run_id: int, summary_text: str):
        """Log a summary for a specific run."""
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO summaries (run_id, timestamp, summary_text) VALUES (?, ?, ?)',
                (run_id, timestamp, summary_text)
            )
            conn.commit()
            logger.info(f"Logged summary for run {run_id}")

    def log_error(self, run_id: int, error_type: str, error_message: str, traceback: str = ''):
        """Log an error for a specific run."""
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO errors (run_id, timestamp, error_type, error_message, traceback) VALUES (?, ?, ?, ?, ?)',
                (run_id, timestamp, error_type, error_message, traceback)
            )
            conn.commit()
            logger.error(f"Logged error {error_type} for run {run_id}: {error_message}")

    def get_system_metrics(self) -> Dict[str, float]:
        """Get system metrics (CPU, memory)."""
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        return {
            'cpu_usage': cpu_usage,
            'memory_usage': memory_info.percent,
            'memory_total': memory_info.total,
            'memory_available': memory_info.available
        }

    def measure_api_latency(self, api_call_func, *args, **kwargs) -> float:
        """Measure the latency of an API call."""
        start_time = time.time()
        try:
            api_call_func(*args, **kwargs)
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # Convert to milliseconds
            logger.info(f"API call latency: {latency:.2f}ms")
            return latency
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            logger.error(f"API call failed with latency {latency:.2f}ms: {str(e)}")
            raise
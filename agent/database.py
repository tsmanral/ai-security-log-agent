import sqlite3
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Path to the SQLite database
DB_PATH = Path(__file__).parent.parent / "data" / "logs.db"

def get_connection() -> sqlite3.Connection:
    """Create and return a connection to the SQLite database."""
    # Ensure directory exists before connecting
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    # Return rows as dictionaries
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database schema."""
    logger.info(f"Initializing database at {DB_PATH}")
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create the parsed_logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parsed_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            hostname TEXT,
            process TEXT,
            pid INTEGER,
            event_type TEXT,
            username TEXT,
            src_ip TEXT,
            src_port INTEGER,
            raw_message TEXT NOT NULL
        )
    ''')
    
    # Create anomalies table to store detection results
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS anomalies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_id INTEGER,
            model_name TEXT,
            anomaly_score REAL,
            is_anomaly BOOLEAN,
            threat_type TEXT,
            mitre_technique TEXT,
            narrative TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(log_id) REFERENCES parsed_logs(id)
        )
    ''')
    
    # Create indexes for faster querying
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON parsed_logs(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_src_ip ON parsed_logs(src_ip)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_username ON parsed_logs(username)')
    
    conn.commit()
    conn.close()
    logger.info("Database schema initialized successfully.")

def insert_log(event: Dict[str, Any]) -> int:
    """
    Insert a single parsed log event into the database.
    
    Args:
        event (Dict[str, Any]): Dictionary containing parsed log fields.
        
    Returns:
        int: The ID of the inserted row.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = '''
        INSERT INTO parsed_logs (
            timestamp, hostname, process, pid, event_type, 
            username, src_ip, src_port, raw_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''
    values = (
        event.get('timestamp'),
        event.get('hostname'),
        event.get('process'),
        event.get('pid'),
        event.get('event_type'),
        event.get('username'),
        event.get('src_ip'),
        event.get('src_port'),
        event.get('raw_message')
    )
    
    cursor.execute(query, values)
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return getattr(cursor, 'lastrowid', 0)

def insert_anomaly(anomaly_data: Dict[str, Any]) -> int:
    """
    Insert an anomaly detection record into the database.
    
    Args:
        anomaly_data (Dict[str, Any]): Dictionary containing anomaly details.
        
    Returns:
        int: The ID of the inserted row.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = '''
        INSERT INTO anomalies (
            log_id, model_name, anomaly_score, is_anomaly,
            threat_type, mitre_technique, narrative
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    '''
    values = (
        anomaly_data.get('log_id'),
        anomaly_data.get('model_name'),
        anomaly_data.get('anomaly_score'),
        anomaly_data.get('is_anomaly'),
        anomaly_data.get('threat_type'),
        anomaly_data.get('mitre_technique'),
        anomaly_data.get('narrative')
    )
    
    cursor.execute(query, values)
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return getattr(cursor, 'lastrowid', 0)

def get_all_logs() -> List[Dict[str, Any]]:
    """Retrieve all parsed logs from the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM parsed_logs ORDER BY timestamp ASC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_recent_logs(limit: int = 1000) -> List[Dict[str, Any]]:
    """Retrieve the most recent logs up to a limit."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM parsed_logs ORDER BY timestamp DESC LIMIT ?', (limit,))
    rows = cursor.fetchall()
    conn.close()
    # Return in chronological order
    result = [dict(row) for row in rows]
    result.reverse()
    return result

if __name__ == "__main__":
    # Configure basic logging for direct script execution
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    init_db()

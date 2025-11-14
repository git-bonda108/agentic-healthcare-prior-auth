"""Database management for prior authorization tracking."""
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path
import json

class PriorAuthDatabase:
    """SQLite database for tracking prior authorizations."""
    
    def __init__(self, db_path: str):
        """Initialize database connection."""
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Prior Authorization Requests table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prior_auths (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_name TEXT NOT NULL,
                file_path TEXT,
                patient_name TEXT,
                provider_name TEXT,
                cpt_codes TEXT,
                icd_codes TEXT,
                status TEXT DEFAULT 'pending',
                submission_date TEXT,
                response_date TEXT,
                response_status TEXT,
                denial_reason TEXT,
                appeal_status TEXT,
                alternative_treatments TEXT,
                notes TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Batch Processing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_number INTEGER,
                total_items INTEGER,
                processed_items INTEGER,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def create_prior_auth(self, data: Dict) -> int:
        """Create a new prior authorization record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO prior_auths (
                file_name, file_path, patient_name, provider_name,
                cpt_codes, icd_codes, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("file_name"),
            data.get("file_path"),
            data.get("patient_name"),
            data.get("provider_name"),
            json.dumps(data.get("cpt_codes", [])),
            json.dumps(data.get("icd_codes", [])),
            data.get("status", "pending"),
            data.get("notes", "")
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id
    
    def update_prior_auth(self, record_id: int, data: Dict):
        """Update a prior authorization record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        for key, value in data.items():
            if key in ["cpt_codes", "icd_codes", "alternative_treatments"]:
                updates.append(f"{key} = ?")
                values.append(json.dumps(value) if isinstance(value, list) else value)
            else:
                updates.append(f"{key} = ?")
                values.append(value)
        
        updates.append("updated_at = ?")
        values.append(datetime.now().isoformat())
        values.append(record_id)
        
        cursor.execute(f"""
            UPDATE prior_auths 
            SET {', '.join(updates)}
            WHERE id = ?
        """, values)
        
        conn.commit()
        conn.close()
    
    def get_prior_auth(self, record_id: int) -> Optional[Dict]:
        """Get a prior authorization record by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM prior_auths WHERE id = ?", (record_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_prior_auths(self, status: Optional[str] = None) -> List[Dict]:
        """Get all prior authorization records, optionally filtered by status."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        if status:
            cursor.execute("SELECT * FROM prior_auths WHERE status = ? ORDER BY created_at DESC", (status,))
        else:
            cursor.execute("SELECT * FROM prior_auths ORDER BY created_at DESC")
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def create_batch(self, batch_number: int, total_items: int) -> int:
        """Create a new batch record."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO batches (batch_number, total_items, processed_items, status)
            VALUES (?, ?, 0, 'pending')
        """, (batch_number, total_items))
        
        batch_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return batch_id
    
    def update_batch(self, batch_id: int, processed_items: int, status: str):
        """Update batch processing status."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE batches 
            SET processed_items = ?, status = ?, completed_at = ?
            WHERE id = ?
        """, (processed_items, status, datetime.now().isoformat() if status == "completed" else None, batch_id))
        
        conn.commit()
        conn.close()

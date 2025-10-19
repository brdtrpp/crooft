"""
Job Status Store - SQLite-based persistent job tracking
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class JobStatus(BaseModel):
    """Job status data model"""
    job_id: str
    project_id: str
    status: Literal["queued", "running", "paused", "completed", "failed", "cancelled"]
    current_stage: Optional[str] = None
    progress_percent: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    config: dict = Field(default_factory=dict)  # Store pipeline config (preset, requirements, etc)


class JobStore:
    """SQLite-based job status storage"""

    def __init__(self, db_path: str = "output/jobs.db"):
        """Initialize job store with SQLite database"""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Create database tables if they don't exist"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_stage TEXT,
                    progress_percent REAL DEFAULT 0.0,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error_message TEXT,
                    config TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS job_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    log_line TEXT,
                    FOREIGN KEY (job_id) REFERENCES jobs(job_id)
                )
            """)

            # Index for faster queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status
                ON jobs(status)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_job_logs_job_id
                ON job_logs(job_id)
            """)

            conn.commit()

    def create_job(self, job_id: str, project_id: str, config: dict = None) -> JobStatus:
        """Create a new job entry"""
        job = JobStatus(
            job_id=job_id,
            project_id=project_id,
            status="queued",
            config=config or {}
        )

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO jobs (job_id, project_id, status, config)
                VALUES (?, ?, ?, ?)
            """, (job.job_id, job.project_id, job.status, json.dumps(job.config)))
            conn.commit()

        return job

    def get_job(self, job_id: str) -> Optional[JobStatus]:
        """Get job by ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM jobs WHERE job_id = ?
            """, (job_id,))

            row = cursor.fetchone()
            if not row:
                return None

            return self._row_to_job(row)

    def update_job(
        self,
        job_id: str,
        status: Optional[str] = None,
        current_stage: Optional[str] = None,
        progress_percent: Optional[float] = None,
        error_message: Optional[str] = None,
        completed_at: Optional[datetime] = None
    ):
        """Update job status"""
        updates = []
        params = []

        if status:
            updates.append("status = ?")
            params.append(status)

            # Auto-set started_at when moving to running
            if status == "running":
                updates.append("started_at = COALESCE(started_at, ?)")
                params.append(datetime.now().isoformat())

        if current_stage:
            updates.append("current_stage = ?")
            params.append(current_stage)

        if progress_percent is not None:
            updates.append("progress_percent = ?")
            params.append(progress_percent)

        if error_message:
            updates.append("error_message = ?")
            params.append(error_message)

        if completed_at:
            updates.append("completed_at = ?")
            params.append(completed_at.isoformat())

        if not updates:
            return

        params.append(job_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f"""
                UPDATE jobs
                SET {', '.join(updates)}
                WHERE job_id = ?
            """, params)
            conn.commit()

    def list_jobs(
        self,
        status: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100
    ) -> List[JobStatus]:
        """List jobs with optional filters"""
        query = "SELECT * FROM jobs WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status)

        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)

            return [self._row_to_job(row) for row in cursor.fetchall()]

    def append_log(self, job_id: str, log_line: str):
        """Append a log line to job"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO job_logs (job_id, log_line)
                VALUES (?, ?)
            """, (job_id, log_line))
            conn.commit()

    def get_logs(self, job_id: str, limit: int = 1000) -> List[dict]:
        """Get recent logs for a job"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT timestamp, log_line
                FROM job_logs
                WHERE job_id = ?
                ORDER BY id DESC
                LIMIT ?
            """, (job_id, limit))

            logs = []
            for row in cursor.fetchall():
                logs.append({
                    'timestamp': row['timestamp'],
                    'log_line': row['log_line']
                })

            return list(reversed(logs))  # Return in chronological order

    def delete_job(self, job_id: str):
        """Delete a job and its logs"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM job_logs WHERE job_id = ?", (job_id,))
            conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
            conn.commit()

    def _row_to_job(self, row: sqlite3.Row) -> JobStatus:
        """Convert database row to JobStatus"""
        return JobStatus(
            job_id=row['job_id'],
            project_id=row['project_id'],
            status=row['status'],
            current_stage=row['current_stage'],
            progress_percent=row['progress_percent'] or 0.0,
            started_at=datetime.fromisoformat(row['started_at']) if row['started_at'] else None,
            completed_at=datetime.fromisoformat(row['completed_at']) if row['completed_at'] else None,
            error_message=row['error_message'],
            config=json.loads(row['config']) if row['config'] else {}
        )

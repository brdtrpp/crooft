"""
Task Queue - In-memory queue for background job processing
"""

import queue
import uuid
from datetime import datetime
from typing import Optional, List
from .job_store import JobStore, JobStatus


class PipelineTask:
    """Represents a pipeline execution task"""

    def __init__(
        self,
        job_id: str,
        project_id: str,
        config: dict
    ):
        self.job_id = job_id
        self.project_id = project_id
        self.config = config  # Contains: preset, use_lore_db, requirements, resume_from


class TaskQueue:
    """In-memory task queue with persistent job status tracking"""

    def __init__(self, job_store: Optional[JobStore] = None):
        """Initialize task queue"""
        self.job_store = job_store or JobStore()
        self._queue = queue.Queue()
        self._active_jobs = {}  # job_id -> PipelineTask (currently executing)
        self._pause_requests = set()  # job_ids that should pause
        self._cancel_requests = set()  # job_ids that should cancel

    def enqueue_pipeline(
        self,
        project_id: str,
        preset: Optional[str] = None,
        use_lore_db: bool = True,
        requirements: Optional[dict] = None,
        resume_from: Optional[str] = None
    ) -> str:
        """
        Enqueue a pipeline execution job

        Args:
            project_id: Project identifier
            preset: Model preset name
            use_lore_db: Whether to use Pinecone lore database
            requirements: Pipeline requirements dict
            resume_from: Optional stage to resume from

        Returns:
            job_id: Unique job identifier
        """
        job_id = str(uuid.uuid4())

        config = {
            'preset': preset,
            'use_lore_db': use_lore_db,
            'requirements': requirements or {},
            'resume_from': resume_from
        }

        # Create job in database
        self.job_store.create_job(job_id, project_id, config)

        # Add to queue
        task = PipelineTask(job_id, project_id, config)
        self._queue.put(task)

        return job_id

    def get_next_task(self, timeout: float = 1.0) -> Optional[PipelineTask]:
        """
        Get next task from queue (blocks with timeout)

        Args:
            timeout: Seconds to wait for task

        Returns:
            PipelineTask or None if timeout
        """
        try:
            task = self._queue.get(timeout=timeout)
            self._active_jobs[task.job_id] = task
            return task
        except queue.Empty:
            return None

    def mark_task_complete(self, job_id: str):
        """Mark task as complete and remove from active jobs"""
        if job_id in self._active_jobs:
            del self._active_jobs[job_id]

    def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """Get current status of a job"""
        return self.job_store.get_job(job_id)

    def list_jobs(
        self,
        status: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 100
    ) -> List[JobStatus]:
        """List jobs with optional filters"""
        return self.job_store.list_jobs(status=status, project_id=project_id, limit=limit)

    def update_job_status(
        self,
        job_id: str,
        status: Optional[str] = None,
        current_stage: Optional[str] = None,
        progress_percent: Optional[float] = None,
        error_message: Optional[str] = None
    ):
        """Update job status in database"""
        completed_at = datetime.now() if status in ("completed", "failed", "cancelled") else None

        self.job_store.update_job(
            job_id=job_id,
            status=status,
            current_stage=current_stage,
            progress_percent=progress_percent,
            error_message=error_message,
            completed_at=completed_at
        )

    def append_log(self, job_id: str, log_line: str):
        """Append log line to job"""
        self.job_store.append_log(job_id, log_line)

    def get_logs(self, job_id: str, limit: int = 1000) -> List[dict]:
        """Get logs for a job"""
        return self.job_store.get_logs(job_id, limit)

    def pause_job(self, job_id: str) -> bool:
        """Request job to pause (will pause at next checkpoint)"""
        if job_id in self._active_jobs:
            self._pause_requests.add(job_id)
            self.update_job_status(job_id, status="paused")
            return True
        return False

    def cancel_job(self, job_id: str) -> bool:
        """Request job to cancel (will stop at next checkpoint)"""
        if job_id in self._active_jobs:
            self._cancel_requests.add(job_id)
            self.update_job_status(job_id, status="cancelled")
            return True
        return False

    def should_pause(self, job_id: str) -> bool:
        """Check if job should pause"""
        return job_id in self._pause_requests

    def should_cancel(self, job_id: str) -> bool:
        """Check if job should cancel"""
        return job_id in self._cancel_requests

    def clear_pause_request(self, job_id: str):
        """Clear pause request (when resuming)"""
        self._pause_requests.discard(job_id)

    def clear_cancel_request(self, job_id: str):
        """Clear cancel request"""
        self._cancel_requests.discard(job_id)

    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused job

        Creates a new task with resume_from set to last checkpoint
        """
        job = self.get_job_status(job_id)
        if not job or job.status != "paused":
            return False

        # Create new task with resume capability
        config = job.config.copy()
        config['resume_from'] = job.current_stage

        new_job_id = self.enqueue_pipeline(
            project_id=job.project_id,
            preset=config.get('preset'),
            use_lore_db=config.get('use_lore_db', True),
            requirements=config.get('requirements'),
            resume_from=config.get('resume_from')
        )

        # Link old job to new job in logs
        self.append_log(job_id, f"Resumed as job {new_job_id}")
        self.append_log(new_job_id, f"Resuming from job {job_id}")

        return True

    def get_queue_size(self) -> int:
        """Get number of pending tasks in queue"""
        return self._queue.qsize()

    def get_active_jobs(self) -> List[str]:
        """Get list of currently active job IDs"""
        return list(self._active_jobs.keys())

    def delete_job(self, job_id: str):
        """Delete a job from database"""
        self.job_store.delete_job(job_id)

"""
Background Worker - Executes pipeline jobs in separate thread
"""

import threading
import time
import traceback
from typing import Optional, Callable
from datetime import datetime

from .task_queue import TaskQueue, PipelineTask
from .state_manager import StateManager


class PipelineWorker:
    """Background worker that executes pipeline jobs"""

    def __init__(
        self,
        task_queue: TaskQueue,
        state_manager: Optional[StateManager] = None,
        output_dir: str = "output",
        manuscript_dir: str = "manuscripts"
    ):
        """
        Initialize pipeline worker

        Args:
            task_queue: Task queue to consume from
            state_manager: State manager for checkpoints
            output_dir: Directory for checkpoints
            manuscript_dir: Directory for final manuscripts
        """
        self.task_queue = task_queue
        self.state_manager = state_manager or StateManager(output_dir=output_dir)
        self.output_dir = output_dir
        self.manuscript_dir = manuscript_dir

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_job_id: Optional[str] = None

    def start(self):
        """Start the background worker thread"""
        if self._running:
            return

        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        print("[Worker] Background worker started")

    def stop(self):
        """Stop the background worker thread"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        print("[Worker] Background worker stopped")

    def is_running(self) -> bool:
        """Check if worker is running"""
        return self._running

    def get_current_job_id(self) -> Optional[str]:
        """Get currently executing job ID"""
        return self._current_job_id

    def _worker_loop(self):
        """Main worker loop - polls queue and executes jobs"""
        while self._running:
            try:
                # Get next task (blocks for 1 second)
                task = self.task_queue.get_next_task(timeout=1.0)

                if task:
                    self._execute_task(task)

            except Exception as e:
                print(f"[Worker] Unexpected error in worker loop: {e}")
                traceback.print_exc()
                time.sleep(1)

    def _execute_task(self, task: PipelineTask):
        """
        Execute a single pipeline task

        Args:
            task: Pipeline task to execute
        """
        self._current_job_id = task.job_id

        try:
            self._log(task.job_id, f"Starting pipeline for project: {task.project_id}")
            self.task_queue.update_job_status(task.job_id, status="running")

            # Import here to avoid circular imports
            from pipeline import FictionPipeline

            # Load project from checkpoint
            project = self.state_manager.load_state(task.project_id)

            if not project:
                raise ValueError(f"Project not found: {task.project_id}")

            self._log(task.job_id, f"Loaded project: {project.series.title}")

            # Determine resume point if requested
            resume_from = task.config.get('resume_from')
            if resume_from:
                self._log(task.job_id, f"Resuming from stage: {resume_from}")

            # Initialize pipeline
            pipeline = FictionPipeline(
                project_id=task.project_id,
                output_dir=self.output_dir,
                preset=task.config.get('preset'),
                use_lore_db=task.config.get('use_lore_db', True),
                requirements=task.config.get('requirements', {})
            )

            # Create progress callback
            def progress_callback(stage: str, progress: float):
                """Called by pipeline to report progress"""
                # Check for pause/cancel requests
                if self.task_queue.should_cancel(task.job_id):
                    self._log(task.job_id, "Cancellation requested")
                    raise CancelledError("Job cancelled by user")

                if self.task_queue.should_pause(task.job_id):
                    self._log(task.job_id, "Pause requested")
                    raise PausedError("Job paused by user")

                # Update status
                self.task_queue.update_job_status(
                    task.job_id,
                    current_stage=stage,
                    progress_percent=progress
                )
                self._log(task.job_id, f"Progress: {stage} - {progress:.1f}%")

            # Run pipeline with progress tracking
            final_project = pipeline.run(
                project,
                progress_callback=progress_callback,
                resume_from=resume_from
            )

            # Export final manuscript
            self._log(task.job_id, "Exporting final manuscript...")
            pipeline.export_manuscript(final_project, self.manuscript_dir)

            # Mark as complete
            self.task_queue.update_job_status(
                task.job_id,
                status="completed",
                progress_percent=100.0
            )
            self._log(task.job_id, "Pipeline completed successfully!")

        except PausedError as e:
            self._log(task.job_id, f"Job paused: {e}")
            self.task_queue.update_job_status(
                task.job_id,
                status="paused"
            )

        except CancelledError as e:
            self._log(task.job_id, f"Job cancelled: {e}")
            self.task_queue.update_job_status(
                task.job_id,
                status="cancelled"
            )

        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            self._log(task.job_id, f"ERROR: {error_msg}")
            self._log(task.job_id, traceback.format_exc())

            self.task_queue.update_job_status(
                task.job_id,
                status="failed",
                error_message=error_msg
            )

        finally:
            # Clean up
            self.task_queue.mark_task_complete(task.job_id)
            self.task_queue.clear_pause_request(task.job_id)
            self.task_queue.clear_cancel_request(task.job_id)
            self._current_job_id = None

    def _log(self, job_id: str, message: str):
        """Log a message for a job"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        self.task_queue.append_log(job_id, log_line)
        print(f"[Job {job_id[:8]}] {message}")


class PausedError(Exception):
    """Raised when job is paused"""
    pass


class CancelledError(Exception):
    """Raised when job is cancelled"""
    pass

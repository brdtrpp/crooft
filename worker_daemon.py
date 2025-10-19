#!/usr/bin/env python3
"""
Background Worker Daemon - Runs independently of Streamlit
This worker continuously processes jobs from the queue, even when the browser is closed.
"""

import sys
import time
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.task_queue import TaskQueue
from utils.background_worker import PipelineWorker

# Global worker reference for signal handling
worker = None

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n[Worker Daemon] Received signal {signum}, shutting down...")
    if worker:
        worker.stop()
    sys.exit(0)

def main():
    """Main daemon loop"""
    global worker

    print("[Worker Daemon] Starting background worker...")
    print("[Worker Daemon] This worker runs independently of the web UI")
    print("[Worker Daemon] Jobs will continue even if you close your browser")
    print("[Worker Daemon] Press Ctrl+C to stop")
    print()

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize queue and worker
    task_queue = TaskQueue()
    worker = PipelineWorker(task_queue)

    # Start worker
    worker.start()

    print(f"[Worker Daemon] Worker started successfully!")
    print(f"[Worker Daemon] Queue size: {task_queue.get_queue_size()}")
    print(f"[Worker Daemon] Active jobs: {len(task_queue.get_active_jobs())}")
    print()

    # Keep daemon alive
    try:
        while True:
            time.sleep(10)

            # Periodic status update
            queue_size = task_queue.get_queue_size()
            active_jobs = task_queue.get_active_jobs()

            if queue_size > 0 or active_jobs:
                print(f"[Worker Daemon] Status - Queue: {queue_size}, Active: {len(active_jobs)}")

    except KeyboardInterrupt:
        print("\n[Worker Daemon] Keyboard interrupt received")
        signal_handler(signal.SIGINT, None)

if __name__ == "__main__":
    main()

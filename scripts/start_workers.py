#!/usr/bin/env python3
"""
Start RQ workers for background task processing

Usage:
    python scripts/start_workers.py                    # Start all workers
    python scripts/start_workers.py --queue parsing    # Start parsing queue only
    python scripts/start_workers.py --workers 5        # Start 5 workers
    python scripts/start_workers.py --daemon           # Run as daemon
"""
import sys
import os
import time
import argparse
import subprocess
import signal
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.workers import WorkerConfig
import redis
from rq import Worker, Queue, Connection

# Color output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(message, color=None):
    """Print colored log message"""
    if color:
        print(f"{color}{message}{Colors.END}")
    else:
        print(message)

def check_redis():
    """Check if Redis is running"""
    try:
        r = redis.from_url(WorkerConfig.REDIS_URL)
        r.ping()
        log("✓ Redis connection OK", Colors.GREEN)
        return True
    except redis.ConnectionError:
        log("✗ Redis connection failed", Colors.RED)
        log("  Start Redis with: redis-server", Colors.YELLOW)
        return False

def start_worker(queue_name, worker_name=None, burst=False):
    """
    Start a single RQ worker

    Args:
        queue_name: Queue to listen on
        worker_name: Optional worker name
        burst: If True, worker exits after completing all jobs
    """
    try:
        redis_conn = redis.from_url(WorkerConfig.REDIS_URL)

        with Connection(redis_conn):
            queue = Queue(queue_name)
            worker = Worker([queue], name=worker_name)

            log(f"✓ Starting worker for queue '{queue_name}'", Colors.GREEN)
            if worker_name:
                log(f"  Worker name: {worker_name}", Colors.BLUE)

            # Start worker (blocking)
            worker.work(burst=burst)

    except KeyboardInterrupt:
        log("\n✓ Worker stopped by user", Colors.YELLOW)
    except Exception as e:
        log(f"✗ Worker error: {e}", Colors.RED)
        raise

def start_workers_multiprocess(queue_configs):
    """
    Start multiple workers as separate processes

    Args:
        queue_configs: List of (queue_name, worker_count) tuples
    """
    processes = []

    def signal_handler(sig, frame):
        log("\n✓ Stopping all workers...", Colors.YELLOW)
        for proc in processes:
            proc.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start worker processes
    for queue_name, worker_count in queue_configs:
        for i in range(worker_count):
            worker_name = f"{queue_name}-worker-{i+1}"

            # Start worker as subprocess
            proc = subprocess.Popen([
                sys.executable,
                __file__,
                '--queue', queue_name,
                '--name', worker_name,
                '--single'
            ])

            processes.append(proc)
            log(f"✓ Started {worker_name} (PID: {proc.pid})", Colors.GREEN)
            time.sleep(0.5)  # Stagger starts

    log(f"\n✓ All {len(processes)} workers started", Colors.GREEN)
    log("  Press Ctrl+C to stop all workers\n", Colors.YELLOW)

    # Wait for all processes
    try:
        for proc in processes:
            proc.wait()
    except KeyboardInterrupt:
        log("\n✓ Stopping all workers...", Colors.YELLOW)
        for proc in processes:
            proc.terminate()

def get_worker_stats():
    """Get statistics about running workers"""
    try:
        redis_conn = redis.from_url(WorkerConfig.REDIS_URL)

        with Connection(redis_conn):
            workers = Worker.all()

            if not workers:
                log("No workers currently running", Colors.YELLOW)
                return

            log(f"\n✓ {len(workers)} workers running:\n", Colors.GREEN)

            for worker in workers:
                state = worker.get_state()
                current_job = worker.get_current_job()

                # Color based on state
                if state == 'busy':
                    color = Colors.BLUE
                elif state == 'idle':
                    color = Colors.GREEN
                else:
                    color = Colors.YELLOW

                log(f"  {worker.name}", color)
                log(f"    State: {state}")
                log(f"    Queues: {[q.name for q in worker.queues]}")
                log(f"    Jobs: {worker.successful_job_count} success, {worker.failed_job_count} failed")

                if current_job:
                    log(f"    Current: {current_job.func_name}")

                log("")

    except redis.ConnectionError:
        log("✗ Cannot connect to Redis", Colors.RED)
    except Exception as e:
        log(f"✗ Error: {e}", Colors.RED)

def get_queue_stats():
    """Get statistics about queues"""
    try:
        redis_conn = redis.from_url(WorkerConfig.REDIS_URL)

        with Connection(redis_conn):
            log("\n✓ Queue Statistics:\n", Colors.GREEN)

            for queue_name in WorkerConfig.QUEUE_NAMES:
                queue = Queue(queue_name, connection=redis_conn)
                pending = len(queue)

                # Get failed job count
                from rq.registry import FailedJobRegistry
                failed_registry = FailedJobRegistry(queue_name, connection=redis_conn)
                failed = len(failed_registry)

                color = Colors.GREEN if pending == 0 else Colors.YELLOW

                log(f"  {queue_name}:", color)
                log(f"    Pending: {pending}")
                log(f"    Failed: {failed}")
                log("")

    except redis.ConnectionError:
        log("✗ Cannot connect to Redis", Colors.RED)
    except Exception as e:
        log(f"✗ Error: {e}", Colors.RED)

def main():
    parser = argparse.ArgumentParser(description='Manage RQ workers for background tasks')
    parser.add_argument('--queue', type=str, help='Queue name (parsing, ai, notion, default)')
    parser.add_argument('--workers', type=int, help='Number of workers to start')
    parser.add_argument('--name', type=str, help='Worker name')
    parser.add_argument('--burst', action='store_true', help='Exit after completing jobs')
    parser.add_argument('--single', action='store_true', help='Start single worker (internal use)')
    parser.add_argument('--stats', action='store_true', help='Show worker and queue statistics')
    parser.add_argument('--daemon', action='store_true', help='Run as background daemon')

    args = parser.parse_args()

    # Check Redis connection
    if not check_redis():
        sys.exit(1)

    # Show statistics
    if args.stats:
        get_worker_stats()
        get_queue_stats()
        sys.exit(0)

    # Start single worker (called by subprocess)
    if args.single:
        queue_name = args.queue or WorkerConfig.DEFAULT_QUEUE
        start_worker(queue_name, worker_name=args.name, burst=args.burst)
        sys.exit(0)

    # Start specific queue
    if args.queue:
        worker_count = args.workers or 1
        queue_configs = [(args.queue, worker_count)]
    else:
        # Start all queues with recommended counts
        queue_configs = [
            ('parsing', WorkerConfig.WORKER_COUNT_PARSING),
            ('ai', WorkerConfig.WORKER_COUNT_AI),
            ('notion', WorkerConfig.WORKER_COUNT_NOTION),
        ]

    log("\n🚀 Starting RQ Workers for Notion KB Manager\n", Colors.BLUE)
    log(f"Redis URL: {WorkerConfig.REDIS_URL}", Colors.BLUE)
    log(f"Queues: {', '.join([f'{q} ({c} workers)' for q, c in queue_configs])}\n", Colors.BLUE)

    # Start workers
    start_workers_multiprocess(queue_configs)

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Test the async task processing system

This script tests:
1. Redis connection
2. Queue creation
3. Job enqueueing
4. Worker processing
5. Task status tracking
"""
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import redis
from rq import Queue, Worker
from app import create_app, db
from app.services.background_task_service import get_background_task_service
from config.workers import WorkerConfig

# Color output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def log(message, color=None, status=None):
    """Print colored log message with status indicator"""
    if status == 'success':
        indicator = f"{Colors.GREEN}✓{Colors.END}"
    elif status == 'error':
        indicator = f"{Colors.RED}✗{Colors.END}"
    elif status == 'info':
        indicator = f"{Colors.BLUE}ℹ{Colors.END}"
    else:
        indicator = ""

    if color:
        print(f"{indicator} {color}{message}{Colors.END}")
    else:
        print(f"{indicator} {message}")

def test_redis_connection():
    """Test 1: Redis connection"""
    log("\n[Test 1] Redis Connection", Colors.BLUE)

    try:
        r = redis.from_url(WorkerConfig.REDIS_URL)
        r.ping()

        info = r.info()
        log(f"Connected to Redis {info.get('redis_version')}", status='success')
        log(f"  Memory used: {info.get('used_memory_human')}")
        log(f"  Connected clients: {info.get('connected_clients')}")
        return True
    except redis.ConnectionError as e:
        log(f"Failed to connect to Redis: {e}", status='error')
        log("Start Redis with: redis-server", Colors.YELLOW)
        return False

def test_queue_creation():
    """Test 2: Queue creation"""
    log("\n[Test 2] Queue Creation", Colors.BLUE)

    try:
        r = redis.from_url(WorkerConfig.REDIS_URL)

        for queue_name in WorkerConfig.QUEUE_NAMES:
            q = Queue(queue_name, connection=r)
            log(f"Queue '{queue_name}' created (size: {len(q)})", status='success')

        return True
    except Exception as e:
        log(f"Failed to create queues: {e}", status='error')
        return False

def test_worker_availability():
    """Test 3: Worker availability"""
    log("\n[Test 3] Worker Availability", Colors.BLUE)

    try:
        r = redis.from_url(WorkerConfig.REDIS_URL)
        workers = Worker.all(connection=r)

        if workers:
            log(f"Found {len(workers)} active workers", status='success')
            for worker in workers[:3]:
                log(f"  - {worker.name} ({worker.get_state()})")
            return True
        else:
            log("No workers running", status='info')
            log("Start workers with: python scripts/start_workers.py", Colors.YELLOW)
            return False

    except Exception as e:
        log(f"Failed to check workers: {e}", status='error')
        return False

def test_job_enqueueing():
    """Test 4: Job enqueueing"""
    log("\n[Test 4] Job Enqueueing", Colors.BLUE)

    try:
        r = redis.from_url(WorkerConfig.REDIS_URL)
        q = Queue('default', connection=r)

        # Define a simple test job
        def test_job(x, y):
            """Simple addition job"""
            time.sleep(1)
            return x + y

        # Enqueue job
        job = q.enqueue(test_job, 5, 10, timeout=30)
        log(f"Job enqueued: {job.id}", status='success')
        log(f"  Function: {job.func_name}")
        log(f"  Status: {job.get_status()}")

        # Wait for job to complete (if workers running)
        max_wait = 10
        waited = 0
        while job.get_status() not in ['finished', 'failed'] and waited < max_wait:
            time.sleep(1)
            waited += 1

        if job.get_status() == 'finished':
            log(f"Job completed: result = {job.result}", status='success')
            return True
        elif job.get_status() == 'failed':
            log(f"Job failed: {job.exc_info}", status='error')
            return False
        else:
            log(f"Job still pending (status: {job.get_status()})", status='info')
            log("Workers may not be running", Colors.YELLOW)
            return False

    except Exception as e:
        log(f"Failed to enqueue job: {e}", status='error')
        return False

def test_background_task_service():
    """Test 5: Background task service"""
    log("\n[Test 5] Background Task Service", Colors.BLUE)

    try:
        app = create_app('development')

        with app.app_context():
            service = get_background_task_service()

            # Create a test task
            task = service.create_task(
                type='test',
                total_items=3,
                config={'test': True},
                queue_name='default'
            )

            log(f"Created task {task.id}", status='success')
            log(f"  Type: {task.type}")
            log(f"  Status: {task.status}")
            log(f"  Total items: {task.total_items}")

            # Create task items
            for i in range(3):
                item = service.create_task_item(
                    task_id=task.id,
                    item_id=i+1,
                    item_type='test_item'
                )
                log(f"  Created item {item.item_id}")

            # Test progress update
            service.update_item_status(task.id, 1, 'completed')
            service.update_task_progress(task.id)

            task_status = service.get_task_status(task.id)
            log(f"Task progress: {task_status['progress']}%", status='success')
            log(f"  Completed: {task_status['completed_items']}/{task_status['total_items']}")

            # Cleanup
            db.session.delete(task)
            db.session.commit()

            return True

    except Exception as e:
        log(f"Failed to test task service: {e}", status='error')
        import traceback
        traceback.print_exc()
        return False

def test_queue_statistics():
    """Test 6: Queue statistics"""
    log("\n[Test 6] Queue Statistics", Colors.BLUE)

    try:
        r = redis.from_url(WorkerConfig.REDIS_URL)

        from rq.registry import (
            StartedJobRegistry,
            FinishedJobRegistry,
            FailedJobRegistry,
            ScheduledJobRegistry
        )

        for queue_name in ['parsing', 'ai', 'notion', 'default']:
            q = Queue(queue_name, connection=r)

            # Get registries
            started = StartedJobRegistry(queue_name, connection=r)
            finished = FinishedJobRegistry(queue_name, connection=r)
            failed = FailedJobRegistry(queue_name, connection=r)
            scheduled = ScheduledJobRegistry(queue_name, connection=r)

            log(f"Queue '{queue_name}':", status='success')
            log(f"  Pending: {len(q)}")
            log(f"  Running: {len(started)}")
            log(f"  Finished: {len(finished)}")
            log(f"  Failed: {len(failed)}")
            log(f"  Scheduled: {len(scheduled)}")

        return True

    except Exception as e:
        log(f"Failed to get queue stats: {e}", status='error')
        return False

def main():
    """Run all async system tests"""
    log("=" * 60, Colors.BLUE)
    log("Async Task Processing System Test Suite", Colors.BLUE)
    log("=" * 60, Colors.BLUE)

    tests = [
        ("Redis Connection", test_redis_connection),
        ("Queue Creation", test_queue_creation),
        ("Worker Availability", test_worker_availability),
        ("Job Enqueueing", test_job_enqueueing),
        ("Background Task Service", test_background_task_service),
        ("Queue Statistics", test_queue_statistics),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            log(f"\n[Error] {test_name} crashed: {e}", Colors.RED)
            results.append((test_name, False))

    # Summary
    log("\n" + "=" * 60, Colors.BLUE)
    log("Test Summary", Colors.BLUE)
    log("=" * 60, Colors.BLUE)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        log(f"  {test_name}: {status}", color)

    log(f"\nTotal: {passed}/{total} tests passed", Colors.BLUE)

    if passed == total:
        log("\n✓ All tests passed! Async system is ready.", Colors.GREEN)
        return 0
    else:
        log(f"\n✗ {total - passed} test(s) failed.", Colors.RED)
        return 1

if __name__ == '__main__':
    sys.exit(main())

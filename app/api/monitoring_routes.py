"""
Monitoring API routes for background workers and queues
"""
from flask import Blueprint
from app.services.background_task_service import get_background_task_service
from app.utils.response import success_response, error_response
from config.workers import WorkerConfig
from redis.exceptions import ConnectionError as RedisConnectionError
import logging

logger = logging.getLogger(__name__)

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')


@monitoring_bp.route('/workers', methods=['GET'])
def get_workers():
    """
    Get status of all workers

    Response (200):
        {
          "success": true,
          "workers": [
            {
              "name": "worker-1.12345",
              "queues": ["parsing-queue"],
              "state": "busy",
              "current_job": "job-uuid",
              "successful_job_count": 45,
              "failed_job_count": 2,
              "birth_date": "2026-01-13T10:00:00"
            }
          ],
          "total_workers": 5
        }
    """
    try:
        task_service = get_background_task_service()
        redis_conn = task_service._get_redis_connection()

        from rq import Worker

        workers = Worker.all(connection=redis_conn)
        worker_list = []

        for worker in workers:
            worker_info = {
                'name': worker.name,
                'queues': [q.name for q in worker.queues],
                'state': worker.get_state(),
                'current_job': worker.get_current_job_id(),
                'successful_job_count': worker.successful_job_count,
                'failed_job_count': worker.failed_job_count,
                'birth_date': worker.birth_date.isoformat() if worker.birth_date else None,
                'last_heartbeat': worker.last_heartbeat.isoformat() if hasattr(worker, 'last_heartbeat') and worker.last_heartbeat else None
            }
            worker_list.append(worker_info)

        return success_response(
            data={
                'workers': worker_list,
                'total_workers': len(worker_list)
            }
        )

    except RedisConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        return error_response('SYS_002', 'Redis connection failed', None, 503)
    except Exception as e:
        logger.error(f"Failed to get workers: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get workers: {str(e)}', None, 500)


@monitoring_bp.route('/queues', methods=['GET'])
def get_queues():
    """
    Get statistics for all queues

    Response (200):
        {
          "success": true,
          "queues": {
            "parsing-queue": {
              "name": "parsing-queue",
              "count": 5,
              "started_job_registry": 2,
              "finished_job_registry": 100,
              "failed_job_registry": 3,
              "deferred_job_registry": 0,
              "scheduled_job_registry": 1,
              "oldest_job_timestamp": "2026-01-13T10:00:00"
            }
          }
        }
    """
    try:
        task_service = get_background_task_service()
        redis_conn = task_service._get_redis_connection()

        from rq import Queue
        from rq.registry import (
            StartedJobRegistry,
            FinishedJobRegistry,
            FailedJobRegistry,
            DeferredJobRegistry,
            ScheduledJobRegistry
        )

        queue_stats = {}

        for queue_name in WorkerConfig.QUEUE_NAMES:
            queue = Queue(queue_name, connection=redis_conn)

            # Get registries
            started_registry = StartedJobRegistry(queue_name, connection=redis_conn)
            finished_registry = FinishedJobRegistry(queue_name, connection=redis_conn)
            failed_registry = FailedJobRegistry(queue_name, connection=redis_conn)
            deferred_registry = DeferredJobRegistry(queue_name, connection=redis_conn)
            scheduled_registry = ScheduledJobRegistry(queue_name, connection=redis_conn)

            # Get oldest job timestamp
            oldest_job_timestamp = None
            if len(queue) > 0:
                job_ids = queue.job_ids
                if job_ids:
                    from rq.job import Job
                    oldest_job = Job.fetch(job_ids[0], connection=redis_conn)
                    if oldest_job.created_at:
                        oldest_job_timestamp = oldest_job.created_at.isoformat()

            queue_stats[queue_name] = {
                'name': queue_name,
                'count': len(queue),  # Jobs waiting in queue
                'started_job_registry': len(started_registry),  # Currently running
                'finished_job_registry': len(finished_registry),  # Recently completed
                'failed_job_registry': len(failed_registry),  # Failed jobs
                'deferred_job_registry': len(deferred_registry),  # Deferred jobs
                'scheduled_job_registry': len(scheduled_registry),  # Scheduled jobs
                'oldest_job_timestamp': oldest_job_timestamp
            }

        return success_response(data={'queues': queue_stats})

    except RedisConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        return error_response('SYS_002', 'Redis connection failed', None, 503)
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get queue stats: {str(e)}', None, 500)


@monitoring_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """
    Get task processing statistics

    Response (200):
        {
          "success": true,
          "statistics": {
            "total_tasks": 150,
            "completed_tasks": 120,
            "failed_tasks": 10,
            "running_tasks": 20,
            "by_type": {
              "parsing": {"total": 50, "completed": 45, "failed": 3, "running": 2},
              "ai_processing": {"total": 60, "completed": 50, "failed": 5, "running": 5},
              "import": {"total": 40, "completed": 25, "failed": 2, "running": 13}
            },
            "total_items_processed": 500,
            "total_items_failed": 25
          }
        }
    """
    try:
        from app.models.content import ProcessingTask
        from app.models.notion import ImportNotionTask
        from app import db

        # Get ProcessingTask statistics
        processing_tasks = db.session.query(ProcessingTask).all()

        # Aggregate statistics
        stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'running_tasks': 0,
            'pending_tasks': 0,
            'by_type': {},
            'total_items_processed': 0,
            'total_items_failed': 0
        }

        # Aggregate by type
        type_stats = {}

        for task in processing_tasks:
            task_type = task.type
            if task_type not in type_stats:
                type_stats[task_type] = {
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'running': 0,
                    'pending': 0
                }

            type_stats[task_type]['total'] += 1
            stats['total_tasks'] += 1

            if task.status == 'completed':
                type_stats[task_type]['completed'] += 1
                stats['completed_tasks'] += 1
            elif task.status == 'failed':
                type_stats[task_type]['failed'] += 1
                stats['failed_tasks'] += 1
            elif task.status in ('running', 'queued'):
                type_stats[task_type]['running'] += 1
                stats['running_tasks'] += 1
            elif task.status == 'pending':
                type_stats[task_type]['pending'] += 1
                stats['pending_tasks'] += 1

            stats['total_items_processed'] += task.completed_items
            stats['total_items_failed'] += task.failed_items

        # Get ImportNotionTask statistics
        notion_tasks = db.session.query(ImportNotionTask).all()

        for task in notion_tasks:
            task_type = 'notion_import'
            if task_type not in type_stats:
                type_stats[task_type] = {
                    'total': 0,
                    'completed': 0,
                    'failed': 0,
                    'running': 0,
                    'pending': 0
                }

            type_stats[task_type]['total'] += 1
            stats['total_tasks'] += 1

            if task.status == 'completed':
                type_stats[task_type]['completed'] += 1
                stats['completed_tasks'] += 1
            elif task.status == 'failed':
                type_stats[task_type]['failed'] += 1
                stats['failed_tasks'] += 1
            elif task.status in ('running', 'queued'):
                type_stats[task_type]['running'] += 1
                stats['running_tasks'] += 1
            elif task.status == 'pending':
                type_stats[task_type]['pending'] += 1
                stats['pending_tasks'] += 1

            stats['total_items_processed'] += task.completed_items
            stats['total_items_failed'] += task.failed_items

        stats['by_type'] = type_stats

        return success_response(data={'statistics': stats})

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get statistics: {str(e)}', None, 500)


@monitoring_bp.route('/health', methods=['GET'])
def get_health():
    """
    Get system health status

    Response (200):
        {
          "success": true,
          "health": {
            "redis": "connected",
            "redis_version": "7.0.0",
            "workers": {
              "total": 8,
              "active": 7,
              "idle": 1,
              "busy": 3
            },
            "queues_healthy": true,
            "queues": {
              "parsing-queue": {"healthy": true, "pending": 5},
              "ai-queue": {"healthy": true, "pending": 10},
              "notion-queue": {"healthy": true, "pending": 2}
            }
          }
        }
    """
    try:
        task_service = get_background_task_service()
        redis_conn = task_service._get_redis_connection()

        from rq import Worker, Queue

        # Check Redis connection
        try:
            redis_info = redis_conn.info()
            redis_status = 'connected'
            redis_version = redis_info.get('redis_version', 'unknown')
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            redis_status = 'disconnected'
            redis_version = 'unknown'

        # Check workers
        workers = Worker.all(connection=redis_conn)
        worker_stats = {
            'total': len(workers),
            'active': 0,
            'idle': 0,
            'busy': 0
        }

        for worker in workers:
            state = worker.get_state()
            if state == 'busy':
                worker_stats['busy'] += 1
                worker_stats['active'] += 1
            elif state == 'idle':
                worker_stats['idle'] += 1
                worker_stats['active'] += 1

        # Check queues
        queue_health = {}
        queues_healthy = True

        for queue_name in WorkerConfig.QUEUE_NAMES:
            queue = Queue(queue_name, connection=redis_conn)
            pending = len(queue)

            # Consider unhealthy if queue has more than 100 pending jobs
            healthy = pending < 100

            queue_health[queue_name] = {
                'healthy': healthy,
                'pending': pending
            }

            if not healthy:
                queues_healthy = False

        health = {
            'redis': redis_status,
            'redis_version': redis_version,
            'workers': worker_stats,
            'queues_healthy': queues_healthy,
            'queues': queue_health
        }

        # Overall health status
        overall_healthy = (
            redis_status == 'connected' and
            worker_stats['active'] > 0 and
            queues_healthy
        )

        return success_response(
            data={'health': health, 'healthy': overall_healthy}
        )

    except RedisConnectionError as e:
        logger.error(f"Redis connection error: {e}")
        return error_response('SYS_002', 'Redis connection failed', None, 503)
    except Exception as e:
        logger.error(f"Failed to get health: {e}", exc_info=True)
        return error_response('SYS_001', f'Failed to get health: {str(e)}', None, 500)

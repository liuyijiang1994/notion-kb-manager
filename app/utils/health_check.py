"""
Comprehensive Health Check System
Monitors all application components for production readiness
"""
import time
import psutil
import redis
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Tuple
from sqlalchemy import text
from app import db

logger = logging.getLogger(__name__)


class HealthStatus:
    """Health status constants"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthChecker:
    """Comprehensive health check for all system components"""

    def __init__(self):
        self.start_time = datetime.utcnow()
        self.checks = {}

    def check_database(self) -> Tuple[str, Dict[str, Any]]:
        """
        Check database connectivity and performance

        Returns:
            Tuple of (status, details)
        """
        try:
            start = time.time()

            # Test connection
            db.session.execute(text("SELECT 1"))
            response_time = (time.time() - start) * 1000  # Convert to ms

            # Get connection pool stats
            pool_stats = {}
            engine = db.engine
            pool = engine.pool

            if hasattr(pool, 'size'):
                pool_stats = {
                    'size': pool.size(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'checked_in': pool.size() - pool.checkedout()
                }

            # Determine status based on response time
            if response_time < 50:
                status = HealthStatus.HEALTHY
            elif response_time < 200:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY

            return status, {
                'status': status,
                'response_time_ms': round(response_time, 2),
                'connection_pool': pool_stats,
                'message': 'Database connection successful'
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return HealthStatus.UNHEALTHY, {
                'status': HealthStatus.UNHEALTHY,
                'error': str(e),
                'message': 'Database connection failed'
            }

    def check_redis(self) -> Tuple[str, Dict[str, Any]]:
        """
        Check Redis connectivity and performance

        Returns:
            Tuple of (status, details)
        """
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url, socket_connect_timeout=2)

            start = time.time()
            r.ping()
            response_time = (time.time() - start) * 1000

            # Get Redis info
            info = r.info()

            memory_used_mb = info.get('used_memory', 0) / 1024 / 1024
            connected_clients = info.get('connected_clients', 0)

            # Determine status
            if response_time < 10:
                status = HealthStatus.HEALTHY
            elif response_time < 50:
                status = HealthStatus.DEGRADED
            else:
                status = HealthStatus.UNHEALTHY

            return status, {
                'status': status,
                'response_time_ms': round(response_time, 2),
                'connected_clients': connected_clients,
                'memory_used_mb': round(memory_used_mb, 2),
                'version': info.get('redis_version', 'unknown'),
                'message': 'Redis connection successful'
            }

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return HealthStatus.UNHEALTHY, {
                'status': HealthStatus.UNHEALTHY,
                'error': str(e),
                'message': 'Redis connection failed'
            }

    def check_workers(self) -> Tuple[str, Dict[str, Any]]:
        """
        Check RQ worker status

        Returns:
            Tuple of (status, details)
        """
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)

            from rq.worker import Worker

            workers = Worker.all(connection=r)

            total_workers = len(workers)
            active_workers = sum(1 for w in workers if w.get_state() in ['busy', 'idle'])
            busy_workers = sum(1 for w in workers if w.get_state() == 'busy')

            # Worker details by queue
            queue_workers = {}
            queue_names = ['parsing', 'ai', 'notion']

            for queue_name in queue_names:
                from rq import Queue
                q = Queue(queue_name, connection=r)
                q_workers = Worker.all(queue=q)
                queue_workers[queue_name] = len(q_workers)

            # Determine status
            if total_workers == 0:
                status = HealthStatus.UNHEALTHY
                message = "No workers running"
            elif active_workers < total_workers * 0.5:
                status = HealthStatus.DEGRADED
                message = "Some workers inactive"
            else:
                status = HealthStatus.HEALTHY
                message = "Workers operational"

            return status, {
                'status': status,
                'total_workers': total_workers,
                'active_workers': active_workers,
                'busy_workers': busy_workers,
                'idle_workers': active_workers - busy_workers,
                'by_queue': queue_workers,
                'message': message
            }

        except Exception as e:
            logger.error(f"Worker health check failed: {e}")
            return HealthStatus.UNHEALTHY, {
                'status': HealthStatus.UNHEALTHY,
                'error': str(e),
                'message': 'Worker check failed'
            }

    def check_queues(self) -> Tuple[str, Dict[str, Any]]:
        """
        Check RQ queue status

        Returns:
            Tuple of (status, details)
        """
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            r = redis.from_url(redis_url)

            from rq import Queue
            from rq.registry import FailedJobRegistry

            queue_names = ['parsing', 'ai', 'notion']
            queue_stats = {}
            total_pending = 0
            total_failed = 0

            for queue_name in queue_names:
                q = Queue(queue_name, connection=r)
                failed_registry = FailedJobRegistry(queue_name, connection=r)

                pending = len(q)
                failed = len(failed_registry)

                queue_stats[queue_name] = {
                    'pending': pending,
                    'failed': failed
                }

                total_pending += pending
                total_failed += failed

            # Determine status
            if total_pending > 1000:
                status = HealthStatus.UNHEALTHY
                message = "Queues severely backed up"
            elif total_pending > 100:
                status = HealthStatus.DEGRADED
                message = "Queues backed up"
            elif total_failed > 50:
                status = HealthStatus.DEGRADED
                message = "High failure rate"
            else:
                status = HealthStatus.HEALTHY
                message = "Queues healthy"

            return status, {
                'status': status,
                'total_pending': total_pending,
                'total_failed': total_failed,
                'queues': queue_stats,
                'message': message
            }

        except Exception as e:
            logger.error(f"Queue health check failed: {e}")
            return HealthStatus.UNHEALTHY, {
                'status': HealthStatus.UNHEALTHY,
                'error': str(e),
                'message': 'Queue check failed'
            }

    def check_disk_space(self) -> Tuple[str, Dict[str, Any]]:
        """
        Check disk space availability

        Returns:
            Tuple of (status, details)
        """
        try:
            # Check main disk partition
            usage = psutil.disk_usage('/')

            percent_used = usage.percent
            free_gb = usage.free / (1024 ** 3)

            # Check critical directories
            directories = {
                'data': os.getenv('DATABASE_DIR', 'data'),
                'logs': os.getenv('LOG_DIR', 'logs'),
                'backups': os.getenv('BACKUP_FOLDER', 'backups'),
                'cache': os.getenv('CACHE_FOLDER', 'cache')
            }

            dir_stats = {}
            for name, path in directories.items():
                if os.path.exists(path):
                    size = sum(f.stat().st_size for f in Path(path).rglob('*') if f.is_file())
                    dir_stats[name] = round(size / (1024 ** 2), 2)  # MB

            # Determine status
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                message = "Critical: Disk almost full"
            elif percent_used > 80:
                status = HealthStatus.DEGRADED
                message = "Warning: Disk space low"
            else:
                status = HealthStatus.HEALTHY
                message = "Disk space adequate"

            return status, {
                'status': status,
                'total_gb': round(usage.total / (1024 ** 3), 2),
                'used_gb': round(usage.used / (1024 ** 3), 2),
                'free_gb': round(free_gb, 2),
                'percent_used': percent_used,
                'directory_sizes_mb': dir_stats,
                'message': message
            }

        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return HealthStatus.DEGRADED, {
                'status': HealthStatus.DEGRADED,
                'error': str(e),
                'message': 'Disk check failed'
            }

    def check_memory(self) -> Tuple[str, Dict[str, Any]]:
        """
        Check system memory usage

        Returns:
            Tuple of (status, details)
        """
        try:
            memory = psutil.virtual_memory()

            percent_used = memory.percent
            available_gb = memory.available / (1024 ** 3)

            # Determine status
            if percent_used > 90:
                status = HealthStatus.UNHEALTHY
                message = "Critical: Memory almost full"
            elif percent_used > 80:
                status = HealthStatus.DEGRADED
                message = "Warning: Memory usage high"
            else:
                status = HealthStatus.HEALTHY
                message = "Memory usage normal"

            return status, {
                'status': status,
                'total_gb': round(memory.total / (1024 ** 3), 2),
                'used_gb': round(memory.used / (1024 ** 3), 2),
                'available_gb': round(available_gb, 2),
                'percent_used': percent_used,
                'message': message
            }

        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return HealthStatus.DEGRADED, {
                'status': HealthStatus.DEGRADED,
                'error': str(e),
                'message': 'Memory check failed'
            }

    def check_cpu(self) -> Tuple[str, Dict[str, Any]]:
        """
        Check CPU usage

        Returns:
            Tuple of (status, details)
        """
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()

            # Determine status
            if cpu_percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "Critical: CPU overloaded"
            elif cpu_percent > 70:
                status = HealthStatus.DEGRADED
                message = "Warning: CPU usage high"
            else:
                status = HealthStatus.HEALTHY
                message = "CPU usage normal"

            return status, {
                'status': status,
                'percent': cpu_percent,
                'cpu_count': cpu_count,
                'load_average': list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None,
                'message': message
            }

        except Exception as e:
            logger.error(f"CPU check failed: {e}")
            return HealthStatus.DEGRADED, {
                'status': HealthStatus.DEGRADED,
                'error': str(e),
                'message': 'CPU check failed'
            }

    def check_all(self) -> Dict[str, Any]:
        """
        Run all health checks

        Returns:
            Dictionary with comprehensive health status
        """
        # Run all checks
        db_status, db_details = self.check_database()
        redis_status, redis_details = self.check_redis()
        workers_status, workers_details = self.check_workers()
        queues_status, queues_details = self.check_queues()
        disk_status, disk_details = self.check_disk_space()
        memory_status, memory_details = self.check_memory()
        cpu_status, cpu_details = self.check_cpu()

        # Determine overall status
        statuses = [
            db_status,
            redis_status,
            workers_status,
            queues_status,
            disk_status,
            memory_status,
            cpu_status
        ]

        if HealthStatus.UNHEALTHY in statuses:
            overall_status = HealthStatus.UNHEALTHY
        elif HealthStatus.DEGRADED in statuses:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        # Calculate uptime
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()

        return {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat(),
            'version': os.getenv('API_VERSION', '1.0'),
            'environment': os.getenv('FLASK_ENV', 'unknown'),
            'uptime_seconds': int(uptime_seconds),
            'components': {
                'database': db_details,
                'redis': redis_details,
                'workers': workers_details,
                'queues': queues_details,
                'disk': disk_details,
                'memory': memory_details,
                'cpu': cpu_details
            }
        }

    def check_ready(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Readiness check for load balancer

        Checks if service can accept traffic

        Returns:
            Tuple of (is_ready, details)
        """
        try:
            # Check critical components only
            db_status, _ = self.check_database()
            redis_status, _ = self.check_redis()
            workers_status, _ = self.check_workers()

            is_ready = all([
                db_status != HealthStatus.UNHEALTHY,
                redis_status != HealthStatus.UNHEALTHY,
                workers_status != HealthStatus.UNHEALTHY
            ])

            return is_ready, {
                'ready': is_ready,
                'checks': {
                    'database': db_status != HealthStatus.UNHEALTHY,
                    'redis': redis_status != HealthStatus.UNHEALTHY,
                    'workers': workers_status != HealthStatus.UNHEALTHY
                }
            }

        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return False, {
                'ready': False,
                'error': str(e)
            }

    def check_alive(self) -> Dict[str, Any]:
        """
        Liveness check for container orchestration

        Simple check that process is running

        Returns:
            Dictionary with alive status
        """
        return {
            'alive': True,
            'timestamp': datetime.utcnow().isoformat()
        }


# Global health checker instance
_health_checker = None


def get_health_checker() -> HealthChecker:
    """
    Get global health checker instance

    Returns:
        HealthChecker instance
    """
    global _health_checker

    if _health_checker is None:
        _health_checker = HealthChecker()

    return _health_checker

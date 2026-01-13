"""
Performance monitoring and metrics collection
Integrates with Prometheus for metrics export
"""
import time
import psutil
import logging
from functools import wraps
from flask import request, g
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from app import db
import redis
import os

logger = logging.getLogger(__name__)

# ==================== Prometheus Metrics ====================

# Request metrics
request_count = Counter(
    'api_requests_total',
    'Total API requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration in seconds',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

request_size = Histogram(
    'api_request_size_bytes',
    'API request size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

response_size = Histogram(
    'api_response_size_bytes',
    'API response size in bytes',
    ['method', 'endpoint'],
    buckets=[100, 1000, 10000, 100000, 1000000]
)

# Task metrics
task_duration = Histogram(
    'task_duration_seconds',
    'Task execution duration in seconds',
    ['task_type', 'status'],
    buckets=[1, 5, 10, 30, 60, 300, 600, 1800, 3600]
)

task_count = Counter(
    'tasks_total',
    'Total tasks executed',
    ['task_type', 'status']
)

# Queue metrics
queue_size = Gauge(
    'queue_size',
    'Number of jobs in queue',
    ['queue_name']
)

queue_failed = Gauge(
    'queue_failed_jobs',
    'Number of failed jobs in queue',
    ['queue_name']
)

worker_count = Gauge(
    'worker_count',
    'Number of active workers',
    ['queue_name']
)

# Database metrics
db_connections_active = Gauge(
    'db_connections_active',
    'Number of active database connections'
)

db_connections_idle = Gauge(
    'db_connections_idle',
    'Number of idle database connections'
)

db_query_duration = Histogram(
    'db_query_duration_seconds',
    'Database query duration',
    ['operation'],
    buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0]
)

# Redis metrics
redis_connections = Gauge(
    'redis_connections',
    'Number of Redis connections'
)

redis_memory_used = Gauge(
    'redis_memory_used_bytes',
    'Redis memory usage in bytes'
)

# System metrics
system_cpu_percent = Gauge(
    'system_cpu_percent',
    'System CPU usage percentage'
)

system_memory_used = Gauge(
    'system_memory_used_bytes',
    'System memory used in bytes'
)

system_memory_total = Gauge(
    'system_memory_total_bytes',
    'System total memory in bytes'
)

system_disk_used = Gauge(
    'system_disk_used_bytes',
    'Disk space used in bytes',
    ['mount_point']
)

system_disk_total = Gauge(
    'system_disk_total_bytes',
    'Total disk space in bytes',
    ['mount_point']
)

# Application info
app_info = Info(
    'notion_kb_manager',
    'Application information'
)


# ==================== Decorators ====================

def monitor_endpoint(f):
    """
    Decorator to monitor endpoint performance

    Tracks:
    - Request count by method, endpoint, status
    - Request duration
    - Request/response size
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Record start time
        start_time = time.time()

        # Store in g for access in after_request
        g.start_time = start_time
        g.endpoint = request.endpoint or 'unknown'

        # Execute request
        response = f(*args, **kwargs)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        request_count.labels(
            method=request.method,
            endpoint=g.endpoint,
            status=response.status_code
        ).inc()

        request_duration.labels(
            method=request.method,
            endpoint=g.endpoint
        ).observe(duration)

        # Request size
        if request.content_length:
            request_size.labels(
                method=request.method,
                endpoint=g.endpoint
            ).observe(request.content_length)

        # Response size
        if response.content_length:
            response_size.labels(
                method=request.method,
                endpoint=g.endpoint
            ).observe(response.content_length)

        return response

    return decorated_function


def monitor_task(task_type):
    """
    Decorator to monitor task execution

    Usage:
        @monitor_task('parsing')
        def parse_content(link_id):
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            status = 'success'

            try:
                result = f(*args, **kwargs)
                return result
            except Exception as e:
                status = 'failed'
                raise
            finally:
                duration = time.time() - start_time

                # Record metrics
                task_count.labels(
                    task_type=task_type,
                    status=status
                ).inc()

                task_duration.labels(
                    task_type=task_type,
                    status=status
                ).observe(duration)

        return decorated_function
    return decorator


def monitor_db_query(operation):
    """
    Decorator to monitor database query performance

    Usage:
        @monitor_db_query('select')
        def get_links():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()

            try:
                result = f(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                db_query_duration.labels(operation=operation).observe(duration)

        return decorated_function
    return decorator


# ==================== Metrics Collection ====================

def collect_system_metrics():
    """
    Collect system-level metrics (CPU, memory, disk)

    Should be called periodically (e.g., every 15 seconds)
    """
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        system_cpu_percent.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        system_memory_used.set(memory.used)
        system_memory_total.set(memory.total)

        # Disk usage
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                system_disk_used.labels(mount_point=partition.mountpoint).set(usage.used)
                system_disk_total.labels(mount_point=partition.mountpoint).set(usage.total)
            except (PermissionError, OSError):
                pass  # Skip inaccessible partitions

    except Exception as e:
        logger.error(f"Error collecting system metrics: {e}")


def collect_database_metrics():
    """
    Collect database connection pool metrics
    """
    try:
        # Get SQLAlchemy engine
        engine = db.engine

        # Connection pool stats
        pool = engine.pool

        if hasattr(pool, 'size'):
            # Get active connections
            checked_out = pool.checkedout()
            db_connections_active.set(checked_out)

            # Calculate idle connections
            pool_size = pool.size()
            idle = pool_size - checked_out
            db_connections_idle.set(idle)

    except Exception as e:
        logger.error(f"Error collecting database metrics: {e}")


def collect_redis_metrics():
    """
    Collect Redis metrics

    Requires REDIS_URL environment variable
    """
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)

        # Get Redis info
        info = r.info()

        # Connected clients
        redis_connections.set(info.get('connected_clients', 0))

        # Memory usage
        memory_used = info.get('used_memory', 0)
        redis_memory_used.set(memory_used)

    except Exception as e:
        logger.error(f"Error collecting Redis metrics: {e}")


def collect_queue_metrics():
    """
    Collect RQ queue metrics

    Tracks queue size, failed jobs, and worker count
    """
    try:
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        r = redis.from_url(redis_url)

        # Import RQ here to avoid circular import
        from rq import Queue
        from rq.worker import Worker

        # Define queues to monitor
        queue_names = ['parsing', 'ai', 'notion']

        for queue_name in queue_names:
            try:
                q = Queue(queue_name, connection=r)

                # Queue size (pending jobs)
                queue_size.labels(queue_name=queue_name).set(len(q))

                # Failed jobs
                failed_count = len(q.failed_job_registry)
                queue_failed.labels(queue_name=queue_name).set(failed_count)

                # Worker count
                workers = Worker.all(queue=q)
                worker_count.labels(queue_name=queue_name).set(len(workers))

            except Exception as e:
                logger.error(f"Error collecting metrics for queue {queue_name}: {e}")

    except Exception as e:
        logger.error(f"Error collecting queue metrics: {e}")


def collect_all_metrics():
    """
    Collect all metrics at once

    Should be called periodically from a background task
    """
    collect_system_metrics()
    collect_database_metrics()
    collect_redis_metrics()
    collect_queue_metrics()


# ==================== Flask Integration ====================

def init_monitoring(app):
    """
    Initialize monitoring for Flask app

    Registers before/after request handlers for automatic metrics

    Args:
        app: Flask application instance
    """
    # Set application info
    app_info.info({
        'version': app.config.get('API_VERSION', '1.0'),
        'environment': app.config.get('ENV', 'unknown'),
        'python_version': f"{app.config.get('PYTHON_VERSION', 'unknown')}"
    })

    # Before request handler
    @app.before_request
    def before_request_metrics():
        """Record request start time"""
        g.start_time = time.time()
        g.endpoint = request.endpoint or 'unknown'

    # After request handler
    @app.after_request
    def after_request_metrics(response):
        """Record request metrics"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time

            # Record metrics
            request_count.labels(
                method=request.method,
                endpoint=g.endpoint,
                status=response.status_code
            ).inc()

            request_duration.labels(
                method=request.method,
                endpoint=g.endpoint
            ).observe(duration)

            # Request size
            if request.content_length:
                request_size.labels(
                    method=request.method,
                    endpoint=g.endpoint
                ).observe(request.content_length)

            # Response size
            if response.content_length:
                response_size.labels(
                    method=request.method,
                    endpoint=g.endpoint
                ).observe(response.content_length)

        return response

    logger.info("Monitoring initialized")


def get_metrics():
    """
    Get current Prometheus metrics in text format

    Returns:
        Tuple of (metrics_text, content_type)
    """
    # Collect latest metrics
    collect_all_metrics()

    # Generate Prometheus text format
    return generate_latest(), CONTENT_TYPE_LATEST


# ==================== Background Metrics Collection ====================

class MetricsCollector:
    """
    Background task for periodic metrics collection

    Usage:
        collector = MetricsCollector(interval=15)
        collector.start()
    """

    def __init__(self, interval=15):
        """
        Initialize metrics collector

        Args:
            interval: Collection interval in seconds (default: 15)
        """
        self.interval = interval
        self.running = False
        self._thread = None

    def start(self):
        """Start background collection"""
        if self.running:
            return

        self.running = True

        import threading

        def collect_loop():
            while self.running:
                try:
                    collect_all_metrics()
                except Exception as e:
                    logger.error(f"Error in metrics collection: {e}")

                time.sleep(self.interval)

        self._thread = threading.Thread(target=collect_loop, daemon=True)
        self._thread.start()

        logger.info(f"Metrics collector started (interval: {self.interval}s)")

    def stop(self):
        """Stop background collection"""
        self.running = False
        if self._thread:
            self._thread.join()

        logger.info("Metrics collector stopped")


# Global collector instance
_collector = None


def start_metrics_collector(interval=15):
    """
    Start global metrics collector

    Args:
        interval: Collection interval in seconds
    """
    global _collector

    if _collector is None:
        _collector = MetricsCollector(interval=interval)
        _collector.start()


def stop_metrics_collector():
    """Stop global metrics collector"""
    global _collector

    if _collector is not None:
        _collector.stop()
        _collector = None

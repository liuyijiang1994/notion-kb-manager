"""
Background workers for async task processing
"""
from redis import Redis
from rq import Queue
from config.workers import WorkerConfig
import os


def get_redis_connection() -> Redis:
    """Get Redis connection for workers"""
    redis_url = os.getenv('REDIS_URL', WorkerConfig.REDIS_URL)
    return Redis.from_url(redis_url)


def get_queue(queue_name: str) -> Queue:
    """Get RQ queue by name"""
    redis_conn = get_redis_connection()
    return Queue(queue_name, connection=redis_conn)


__all__ = [
    'get_redis_connection',
    'get_queue',
]

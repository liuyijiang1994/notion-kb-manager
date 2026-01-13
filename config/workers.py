"""
Worker configuration for background task processing
"""
import os


class WorkerConfig:
    """Configuration for RQ workers and queues"""

    # Redis connection
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    REDIS_DB = 0

    # Queue names
    QUEUE_NAMES = ['parsing-queue', 'ai-queue', 'notion-queue', 'default']
    PARSING_QUEUE = 'parsing-queue'
    AI_QUEUE = 'ai-queue'
    NOTION_QUEUE = 'notion-queue'
    DEFAULT_QUEUE = 'default'

    # Job timeouts (seconds)
    DEFAULT_TIMEOUT = 180  # 3 minutes
    PARSING_TIMEOUT = 60  # 1 minute per URL
    AI_TIMEOUT = 120  # 2 minutes for AI processing
    NOTION_TIMEOUT = 60  # 1 minute for Notion API

    # Result storage
    DEFAULT_RESULT_TTL = 3600  # Keep job results for 1 hour
    FAILED_JOB_TTL = 86400  # Keep failed jobs for 24 hours

    # Worker counts (for production deployment)
    WORKER_COUNT_PARSING = int(os.getenv('WORKER_COUNT_PARSING', '3'))
    WORKER_COUNT_AI = int(os.getenv('WORKER_COUNT_AI', '2'))
    WORKER_COUNT_NOTION = int(os.getenv('WORKER_COUNT_NOTION', '2'))

    # Retry settings
    MAX_RETRIES = int(os.getenv('MAX_TASK_RETRIES', '3'))
    RETRY_DELAYS = [0, 30, 300]  # Immediate, 30s, 5min

    # Task retention (days)
    TASK_RETENTION_DAYS = int(os.getenv('TASK_RETENTION_DAYS', '7'))
    FAILED_TASK_RETENTION_DAYS = int(os.getenv('FAILED_TASK_RETENTION_DAYS', '30'))

    # Worker heartbeat
    HEARTBEAT_INTERVAL = 30  # seconds
    WORKER_DEAD_THRESHOLD = 120  # Mark worker dead after 2 minutes

    # Monitoring
    ENABLE_RQ_DASHBOARD = os.getenv('ENABLE_RQ_DASHBOARD', 'true').lower() == 'true'
    RQ_DASHBOARD_PORT = int(os.getenv('RQ_DASHBOARD_PORT', '9181'))

    @classmethod
    def get_queue_config(cls, queue_name: str) -> dict:
        """Get configuration for a specific queue"""
        configs = {
            cls.PARSING_QUEUE: {
                'timeout': cls.PARSING_TIMEOUT,
                'result_ttl': cls.DEFAULT_RESULT_TTL,
                'worker_count': cls.WORKER_COUNT_PARSING,
            },
            cls.AI_QUEUE: {
                'timeout': cls.AI_TIMEOUT,
                'result_ttl': cls.DEFAULT_RESULT_TTL,
                'worker_count': cls.WORKER_COUNT_AI,
            },
            cls.NOTION_QUEUE: {
                'timeout': cls.NOTION_TIMEOUT,
                'result_ttl': cls.DEFAULT_RESULT_TTL,
                'worker_count': cls.WORKER_COUNT_NOTION,
            },
            cls.DEFAULT_QUEUE: {
                'timeout': cls.DEFAULT_TIMEOUT,
                'result_ttl': cls.DEFAULT_RESULT_TTL,
                'worker_count': 1,
            },
        }
        return configs.get(queue_name, configs[cls.DEFAULT_QUEUE])

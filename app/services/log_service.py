"""
Log management service for operation logs
"""
import logging
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import or_, desc, func
from app import db
from app.models.system import OperationLog

logger = logging.getLogger(__name__)


class LogService:
    """Service for managing operation logs"""

    def __init__(self):
        self.log_dir = Path(os.getenv('LOG_DIR', 'logs'))
        self.log_dir.mkdir(exist_ok=True, parents=True)

    def create_log(self, level: str, module: str, action: str,
                   message: str, user_id: Optional[str] = None,
                   ip_address: Optional[str] = None) -> int:
        """
        Create a new operation log entry

        Args:
            level: Log level (info/warning/error)
            module: Module name
            action: Action performed
            message: Log message
            user_id: Optional user ID
            ip_address: Optional IP address

        Returns:
            Created log ID
        """
        try:
            log = OperationLog(
                level=level,
                module=module,
                action=action,
                message=message,
                user_id=user_id,
                ip_address=ip_address
            )
            db.session.add(log)
            db.session.commit()

            return log.id

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create log: {e}", exc_info=True)
            raise

    def get_logs(self, level: Optional[str] = None,
                module: Optional[str] = None,
                search: Optional[str] = None,
                start_date: Optional[datetime] = None,
                end_date: Optional[datetime] = None,
                page: int = 1,
                per_page: int = 50) -> Dict[str, Any]:
        """
        Get operation logs with filtering and pagination

        Args:
            level: Filter by level
            module: Filter by module
            search: Search in action and message
            start_date: Filter by start date
            end_date: Filter by end date
            page: Page number
            per_page: Items per page

        Returns:
            Dict with logs and pagination info
        """
        try:
            # Build query
            query = db.session.query(OperationLog)

            # Apply filters
            if level:
                query = query.filter(OperationLog.level == level)

            if module:
                query = query.filter(OperationLog.module == module)

            if search:
                search_term = f'%{search}%'
                query = query.filter(
                    or_(
                        OperationLog.action.ilike(search_term),
                        OperationLog.message.ilike(search_term)
                    )
                )

            if start_date:
                query = query.filter(OperationLog.created_at >= start_date)

            if end_date:
                query = query.filter(OperationLog.created_at <= end_date)

            # Get total count
            total = query.count()

            # Apply sorting and pagination
            query = query.order_by(desc(OperationLog.created_at))
            offset = (page - 1) * per_page
            logs = query.limit(per_page).offset(offset).all()

            # Format results
            items = [
                {
                    'id': log.id,
                    'level': log.level,
                    'module': log.module,
                    'action': log.action,
                    'message': log.message,
                    'user_id': log.user_id,
                    'ip_address': log.ip_address,
                    'created_at': log.created_at.isoformat()
                }
                for log in logs
            ]

            pages = (total + per_page - 1) // per_page

            return {
                'items': items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': pages
                }
            }

        except Exception as e:
            logger.error(f"Failed to get logs: {e}", exc_info=True)
            raise

    def get_log_statistics(self, days: int = 7) -> Dict[str, Any]:
        """
        Get log statistics for recent days

        Args:
            days: Number of recent days

        Returns:
            Dict with statistics
        """
        try:
            start_date = datetime.utcnow() - timedelta(days=days)

            # Total logs
            total_logs = db.session.query(OperationLog).filter(
                OperationLog.created_at >= start_date
            ).count()

            # By level
            by_level = db.session.query(
                OperationLog.level,
                func.count(OperationLog.id)
            ).filter(
                OperationLog.created_at >= start_date
            ).group_by(OperationLog.level).all()

            # By module
            by_module = db.session.query(
                OperationLog.module,
                func.count(OperationLog.id)
            ).filter(
                OperationLog.created_at >= start_date
            ).group_by(OperationLog.module).order_by(
                desc(func.count(OperationLog.id))
            ).limit(10).all()

            # Recent errors
            recent_errors = db.session.query(OperationLog).filter(
                OperationLog.level == 'error',
                OperationLog.created_at >= start_date
            ).order_by(desc(OperationLog.created_at)).limit(10).all()

            return {
                'total_logs': total_logs,
                'by_level': {level: count for level, count in by_level},
                'by_module': {module: count for module, count in by_module},
                'recent_errors': [
                    {
                        'id': log.id,
                        'module': log.module,
                        'action': log.action,
                        'message': log.message,
                        'created_at': log.created_at.isoformat()
                    }
                    for log in recent_errors
                ],
                'period_days': days
            }

        except Exception as e:
            logger.error(f"Failed to get log statistics: {e}", exc_info=True)
            raise

    def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Delete logs older than specified days

        Args:
            days: Keep logs from last N days

        Returns:
            Number of deleted logs
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            deleted = db.session.query(OperationLog).filter(
                OperationLog.created_at < cutoff_date
            ).delete(synchronize_session=False)

            db.session.commit()

            logger.info(f"Cleaned up {deleted} old logs (older than {days} days)")
            return deleted

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to cleanup old logs: {e}", exc_info=True)
            raise

    def export_logs(self, level: Optional[str] = None,
                   module: Optional[str] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None,
                   format: str = 'json') -> List[Dict[str, Any]]:
        """
        Export logs to JSON format

        Args:
            level: Filter by level
            module: Filter by module
            start_date: Filter by start date
            end_date: Filter by end date
            format: Export format (json/csv)

        Returns:
            List of log dictionaries
        """
        try:
            # Build query
            query = db.session.query(OperationLog)

            # Apply filters
            if level:
                query = query.filter(OperationLog.level == level)

            if module:
                query = query.filter(OperationLog.module == module)

            if start_date:
                query = query.filter(OperationLog.created_at >= start_date)

            if end_date:
                query = query.filter(OperationLog.created_at <= end_date)

            # Get all matching logs
            query = query.order_by(OperationLog.created_at)
            logs = query.all()

            # Format for export
            exported = [
                {
                    'id': log.id,
                    'level': log.level,
                    'module': log.module,
                    'action': log.action,
                    'message': log.message,
                    'user_id': log.user_id,
                    'ip_address': log.ip_address,
                    'created_at': log.created_at.isoformat()
                }
                for log in logs
            ]

            logger.info(f"Exported {len(exported)} logs")
            return exported

        except Exception as e:
            logger.error(f"Failed to export logs: {e}", exc_info=True)
            raise

    def get_modules(self) -> List[str]:
        """
        Get list of unique modules

        Returns:
            List of module names
        """
        try:
            modules = db.session.query(OperationLog.module).distinct().all()
            return [module[0] for module in modules]

        except Exception as e:
            logger.error(f"Failed to get modules: {e}", exc_info=True)
            return []


# Singleton instance
_log_service = None


def get_log_service() -> LogService:
    """Get singleton instance of LogService"""
    global _log_service
    if _log_service is None:
        _log_service = LogService()
    return _log_service

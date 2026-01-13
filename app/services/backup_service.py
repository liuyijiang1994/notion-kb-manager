"""
Backup and restore service for database and files
"""
import os
import shutil
import zipfile
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import desc
from app import db
from app.models.system import Backup, BackupFiles

logger = logging.getLogger(__name__)


class BackupService:
    """Service for backup and restore operations"""

    def __init__(self):
        self.backup_dir = Path(os.getenv('BACKUP_DIR', 'backups'))
        self.backup_dir.mkdir(exist_ok=True, parents=True)

        # Database path
        self.db_path = Path(os.getenv('DATABASE_PATH', 'instance/notion_kb.db'))

        # File directories to backup
        self.file_dirs = [
            Path('instance'),  # Database and instance files
            Path('logs'),      # Log files
            Path('uploads')    # Uploaded files (if any)
        ]

    def create_backup(self, backup_type: str = 'manual',
                     include_database: bool = True,
                     include_files: bool = True,
                     retention_days: Optional[int] = None) -> Dict[str, Any]:
        """
        Create a new backup

        Args:
            backup_type: 'manual' or 'auto'
            include_database: Include database file
            include_files: Include application files
            retention_days: Days to keep backup (None = forever)

        Returns:
            Dict with backup info
        """
        try:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_filename = f'backup_{backup_type}_{timestamp}.zip'
            backup_filepath = self.backup_dir / backup_filename

            logger.info(f"Creating backup: {backup_filename}")

            # Create backup record
            expires_at = None
            if retention_days:
                expires_at = datetime.utcnow() + timedelta(days=retention_days)

            backup = Backup(
                filename=backup_filename,
                filepath=str(backup_filepath),
                size=0,  # Will update after creation
                type=backup_type,
                expires_at=expires_at
            )
            db.session.add(backup)
            db.session.flush()

            # Create zip archive
            total_size = 0
            with zipfile.ZipFile(backup_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Backup database
                if include_database and self.db_path.exists():
                    logger.info(f"Backing up database: {self.db_path}")

                    # For SQLite, we need to ensure no writes during backup
                    # In production, use WAL mode or online backup
                    zipf.write(self.db_path, arcname=f'database/{self.db_path.name}')

                    file_size = self.db_path.stat().st_size
                    total_size += file_size

                    backup_file = BackupFiles(
                        backup_id=backup.id,
                        file_type='database',
                        file_path=str(self.db_path),
                        size=file_size
                    )
                    db.session.add(backup_file)

                # Backup files
                if include_files:
                    for dir_path in self.file_dirs:
                        if not dir_path.exists():
                            continue

                        logger.info(f"Backing up directory: {dir_path}")

                        # Add all files in directory
                        for file_path in dir_path.rglob('*'):
                            if file_path.is_file():
                                # Skip database file if already backed up
                                if file_path == self.db_path:
                                    continue

                                arcname = str(file_path.relative_to('.'))
                                zipf.write(file_path, arcname=arcname)

                                file_size = file_path.stat().st_size
                                total_size += file_size

                                backup_file = BackupFiles(
                                    backup_id=backup.id,
                                    file_type=dir_path.name,
                                    file_path=str(file_path),
                                    size=file_size
                                )
                                db.session.add(backup_file)

            # Update backup size
            backup.size = backup_filepath.stat().st_size
            db.session.commit()

            logger.info(f"Backup created successfully: {backup_filename} ({backup.size} bytes)")

            return {
                'success': True,
                'backup_id': backup.id,
                'filename': backup_filename,
                'size': backup.size,
                'total_files_size': total_size,
                'created_at': backup.created_at.isoformat()
            }

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create backup: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def list_backups(self, backup_type: Optional[str] = None,
                    page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """
        List all backups with pagination

        Args:
            backup_type: Filter by type (manual/auto)
            page: Page number
            per_page: Items per page

        Returns:
            Dict with backups and pagination info
        """
        try:
            # Build query
            query = db.session.query(Backup)

            # Apply type filter
            if backup_type:
                query = query.filter(Backup.type == backup_type)

            # Get total count
            total = query.count()

            # Apply pagination and sorting
            query = query.order_by(desc(Backup.created_at))
            offset = (page - 1) * per_page
            backups = query.limit(per_page).offset(offset).all()

            # Format results
            items = []
            for backup in backups:
                # Check if file still exists
                file_exists = Path(backup.filepath).exists()

                # Get file count
                file_count = len(backup.files)

                # Check if expired
                is_expired = backup.expires_at and backup.expires_at < datetime.utcnow()

                items.append({
                    'id': backup.id,
                    'filename': backup.filename,
                    'size': backup.size,
                    'type': backup.type,
                    'file_count': file_count,
                    'file_exists': file_exists,
                    'is_expired': is_expired,
                    'created_at': backup.created_at.isoformat(),
                    'expires_at': backup.expires_at.isoformat() if backup.expires_at else None
                })

            pages = (total + per_page - 1) // per_page

            return {
                'success': True,
                'items': items,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': pages
                }
            }

        except Exception as e:
            logger.error(f"Failed to list backups: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_backup_details(self, backup_id: int) -> Optional[Dict[str, Any]]:
        """
        Get detailed backup information

        Args:
            backup_id: Backup ID

        Returns:
            Dict with backup details or None if not found
        """
        try:
            backup = db.session.query(Backup).get(backup_id)
            if not backup:
                return None

            file_exists = Path(backup.filepath).exists()
            is_expired = backup.expires_at and backup.expires_at < datetime.utcnow()

            # Get files grouped by type
            files_by_type = {}
            for file in backup.files:
                if file.file_type not in files_by_type:
                    files_by_type[file.file_type] = {
                        'count': 0,
                        'total_size': 0
                    }
                files_by_type[file.file_type]['count'] += 1
                files_by_type[file.file_type]['total_size'] += file.size

            return {
                'id': backup.id,
                'filename': backup.filename,
                'filepath': backup.filepath,
                'size': backup.size,
                'type': backup.type,
                'file_exists': file_exists,
                'is_expired': is_expired,
                'files_by_type': files_by_type,
                'total_files': len(backup.files),
                'created_at': backup.created_at.isoformat(),
                'expires_at': backup.expires_at.isoformat() if backup.expires_at else None
            }

        except Exception as e:
            logger.error(f"Failed to get backup details: {e}", exc_info=True)
            return None

    def restore_backup(self, backup_id: int,
                      restore_database: bool = True,
                      restore_files: bool = True) -> Dict[str, Any]:
        """
        Restore from backup

        Args:
            backup_id: Backup ID
            restore_database: Restore database file
            restore_files: Restore application files

        Returns:
            Dict with restore result
        """
        try:
            backup = db.session.query(Backup).get(backup_id)
            if not backup:
                return {
                    'success': False,
                    'error': f'Backup {backup_id} not found'
                }

            backup_path = Path(backup.filepath)
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': f'Backup file not found: {backup.filepath}'
                }

            logger.info(f"Restoring from backup: {backup.filename}")

            restored_files = []

            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # List all files in backup
                file_list = zipf.namelist()

                for file_path in file_list:
                    # Determine if this is database or application file
                    is_database = file_path.startswith('database/')

                    # Skip if not requested
                    if is_database and not restore_database:
                        continue
                    if not is_database and not restore_files:
                        continue

                    # Extract file
                    logger.info(f"Restoring file: {file_path}")

                    # For database files, extract to instance directory
                    if is_database:
                        # Create backup of current database first
                        if self.db_path.exists():
                            backup_current = self.db_path.with_suffix('.db.backup')
                            shutil.copy2(self.db_path, backup_current)
                            logger.info(f"Current database backed up to: {backup_current}")

                        # Extract database
                        zipf.extract(file_path, path='.')

                        # Move to correct location
                        extracted_path = Path(file_path)
                        if extracted_path != self.db_path:
                            shutil.move(str(extracted_path), str(self.db_path))

                    else:
                        # Extract application files
                        zipf.extract(file_path, path='.')

                    restored_files.append(file_path)

            logger.info(f"Restore completed: {len(restored_files)} files restored")

            return {
                'success': True,
                'backup_id': backup_id,
                'restored_files_count': len(restored_files),
                'message': 'Restore completed successfully. Please restart the application.'
            }

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def delete_backup(self, backup_id: int, delete_file: bool = True) -> bool:
        """
        Delete backup

        Args:
            backup_id: Backup ID
            delete_file: Also delete physical file

        Returns:
            True if deleted, False if not found
        """
        try:
            backup = db.session.query(Backup).get(backup_id)
            if not backup:
                return False

            # Delete physical file
            if delete_file:
                backup_path = Path(backup.filepath)
                if backup_path.exists():
                    backup_path.unlink()
                    logger.info(f"Deleted backup file: {backup.filepath}")

            # Delete database records (cascade will delete backup_files)
            db.session.delete(backup)
            db.session.commit()

            logger.info(f"Deleted backup: {backup_id}")
            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to delete backup: {e}", exc_info=True)
            return False

    def cleanup_expired_backups(self) -> Dict[str, Any]:
        """
        Delete expired backups

        Returns:
            Dict with cleanup results
        """
        try:
            # Find expired backups
            expired = db.session.query(Backup).filter(
                Backup.expires_at < datetime.utcnow()
            ).all()

            deleted_count = 0
            for backup in expired:
                if self.delete_backup(backup.id, delete_file=True):
                    deleted_count += 1

            logger.info(f"Cleaned up {deleted_count} expired backups")

            return {
                'success': True,
                'deleted_count': deleted_count
            }

        except Exception as e:
            logger.error(f"Failed to cleanup expired backups: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def get_backup_statistics(self) -> Dict[str, Any]:
        """
        Get backup statistics

        Returns:
            Dict with statistics
        """
        try:
            total_backups = db.session.query(Backup).count()
            manual_backups = db.session.query(Backup).filter_by(type='manual').count()
            auto_backups = db.session.query(Backup).filter_by(type='auto').count()

            # Total size
            from sqlalchemy import func
            total_size = db.session.query(func.sum(Backup.size)).scalar() or 0

            # Expired count
            expired_count = db.session.query(Backup).filter(
                Backup.expires_at < datetime.utcnow()
            ).count()

            # Latest backup
            latest = db.session.query(Backup).order_by(desc(Backup.created_at)).first()

            return {
                'total_backups': total_backups,
                'manual_backups': manual_backups,
                'auto_backups': auto_backups,
                'total_size': total_size,
                'expired_count': expired_count,
                'latest_backup': {
                    'id': latest.id,
                    'filename': latest.filename,
                    'created_at': latest.created_at.isoformat()
                } if latest else None
            }

        except Exception as e:
            logger.error(f"Failed to get backup statistics: {e}", exc_info=True)
            return {}


# Singleton instance
_backup_service = None


def get_backup_service() -> BackupService:
    """Get singleton instance of BackupService"""
    global _backup_service
    if _backup_service is None:
        _backup_service = BackupService()
    return _backup_service

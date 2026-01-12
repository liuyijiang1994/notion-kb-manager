"""
System management database models
"""
from sqlalchemy import Integer, String, Text, DateTime, BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from app.models.base import Base


class Backup(Base):
    """Backup metadata"""
    __tablename__ = 'backup'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    filepath: Mapped[str] = mapped_column(String(1000), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # manual/auto
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    files: Mapped[List["BackupFiles"]] = relationship("BackupFiles", back_populates="backup", cascade="all, delete-orphan")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<Backup(id={self.id}, filename='{self.filename}', type='{self.type}')>"


class BackupFiles(Base):
    """Individual files in backup"""
    __tablename__ = 'backup_files'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    backup_id: Mapped[int] = mapped_column(Integer, ForeignKey('backup.id', ondelete='CASCADE'), nullable=False)
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    # Relationships
    backup: Mapped["Backup"] = relationship("Backup", back_populates="files")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<BackupFiles(id={self.id}, backup_id={self.backup_id}, type='{self.file_type}')>"


class OperationLog(Base):
    """System operation logs"""
    __tablename__ = 'operation_log'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    level: Mapped[str] = mapped_column(String(20), nullable=False)  # info/warning/error
    module: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[Optional[str]] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<OperationLog(id={self.id}, level='{self.level}', module='{self.module}')>"


class Feedback(Base):
    """User feedback"""
    __tablename__ = 'feedback'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # bug/feature/other
    content: Mapped[str] = mapped_column(Text, nullable=False)
    screenshot_path: Mapped[Optional[str]] = mapped_column(String(500))
    user_email: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default='new', nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<Feedback(id={self.id}, type='{self.type}', status='{self.status}')>"

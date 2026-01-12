"""
Configuration-related database models
"""
from sqlalchemy import Integer, String, Boolean, Text, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from app.models.base import Base, TimestampMixin


class ModelConfiguration(Base, TimestampMixin):
    """AI Model configuration with encrypted credentials"""
    __tablename__ = 'model_configuration'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    api_url: Mapped[str] = mapped_column(String(500), nullable=False)
    api_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    timeout: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_limit: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<ModelConfiguration(id={self.id}, name='{self.name}', status='{self.status}')>"


class NotionConfiguration(Base, TimestampMixin):
    """Notion API configuration"""
    __tablename__ = 'notion_configuration'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_token_encrypted: Mapped[str] = mapped_column(Text, nullable=False)
    workspace_id: Mapped[Optional[str]] = mapped_column(String(100))
    workspace_name: Mapped[Optional[str]] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<NotionConfiguration(id={self.id}, workspace='{self.workspace_name}')>"


class ToolParameters(Base):
    """Global tool configuration (singleton table)"""
    __tablename__ = 'tool_parameters'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    quality_threshold: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    render_timeout: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    ocr_language: Mapped[str] = mapped_column(String(20), default='auto', nullable=False)
    batch_size: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    retain_cache: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    export_format: Mapped[str] = mapped_column(String(20), default='excel', nullable=False)
    cache_retention_days: Mapped[int] = mapped_column(Integer, default=7, nullable=False)
    cache_auto_clean: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notification_frequency: Mapped[str] = mapped_column(String(20), default='all', nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ToolParameters(quality_threshold={self.quality_threshold})>"


class UserPreferences(Base):
    """User interface preferences (singleton table)"""
    __tablename__ = 'user_preferences'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    theme: Mapped[str] = mapped_column(String(20), default='system', nullable=False)
    font_size: Mapped[str] = mapped_column(String(20), default='medium', nullable=False)
    panel_layout: Mapped[Optional[dict]] = mapped_column(JSON)
    shortcuts: Mapped[Optional[dict]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<UserPreferences(theme='{self.theme}')>"

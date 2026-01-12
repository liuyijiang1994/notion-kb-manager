"""
Notion integration database models
"""
from sqlalchemy import Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.content import AIProcessedContent


class NotionMapping(Base, TimestampMixin):
    """Field mapping configuration for Notion import"""
    __tablename__ = 'notion_mapping'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    target_location: Mapped[str] = mapped_column(String(200), nullable=False)
    target_hierarchy: Mapped[Optional[list]] = mapped_column(JSON)
    field_mappings: Mapped[dict] = mapped_column(JSON, nullable=False)
    format_settings: Mapped[Optional[dict]] = mapped_column(JSON)

    # Relationships
    notion_imports: Mapped[List["NotionImport"]] = relationship("NotionImport", back_populates="mapping")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<NotionMapping(id={self.id}, name='{self.name}')>"


class NotionImport(Base):
    """Notion import record"""
    __tablename__ = 'notion_import'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content_id: Mapped[int] = mapped_column(Integer, ForeignKey('ai_processed_content.id'), nullable=False)
    mapping_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey('notion_mapping.id'))
    notion_page_id: Mapped[Optional[str]] = mapped_column(String(200))
    notion_url: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    imported_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Relationships
    ai_content: Mapped["AIProcessedContent"] = relationship("AIProcessedContent", back_populates="notion_import")
    mapping: Mapped[Optional["NotionMapping"]] = relationship("NotionMapping", back_populates="notion_imports")

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<NotionImport(id={self.id}, status='{self.status}')>"


class ImportNotionTask(Base):
    """Notion import task tracking"""
    __tablename__ = 'import_notion_task'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # import/sync
    status: Mapped[str] = mapped_column(String(50), default='pending', nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_items: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    config: Mapped[Optional[dict]] = mapped_column(JSON)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    __table_args__ = (
        {'sqlite_autoincrement': True},
    )

    def __repr__(self):
        return f"<ImportNotionTask(id={self.id}, type='{self.type}', status='{self.status}')>"
